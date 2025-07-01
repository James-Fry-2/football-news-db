# src/services/llm_service.py

import json
import asyncio
import hashlib
import time
import re
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime, timedelta
from collections import defaultdict
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain.callbacks.base import BaseCallbackHandler
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import uuid

from .enhanced_search_service import EnhancedSearchService
from .article_service import ArticleService

from ...config.vector_config import (
    OPENAI_API_KEY, OPENAI_CHAT_MODEL,
    LANGSMITH_TRACING, LANGSMITH_ENDPOINT, LANGSMITH_API_KEY, LANGSMITH_PROJECT
)

# Global session store for tools
_session_store = {}

def set_session_for_tools(session_id: str, session: AsyncSession):
    """Store session for tools to access."""
    _session_store[session_id] = session

def get_session_for_tools(session_id: str) -> AsyncSession:
    """Get session for tools."""
    return _session_store.get(session_id)


class QueryClassifier:
    """Classifies queries to determine appropriate caching strategy."""
    
    # Query classification patterns
    FACTUAL_PATTERNS = [
        r'\b(stats?|statistics?|record|career|age|nationality|position|height|weight)\b',
        r'\b(goals?|assists?|appearances?|minutes?|cards?|saves?)\b',
        r'\b(born|birth|club|team|league|transfer|contract)\b',
        r'\b(when|where|how many|what position|which team)\b'
    ]
    
    NEWS_PATTERNS = [
        r'\b(news|latest|recent|today|yesterday|this week|update)\b',
        r'\b(injury|injured|transfer|signed|rumor|report)\b',
        r'\b(match|game|fixture|result|score|win|loss|draw)\b',
        r'\b(happening|occurred|announced|confirmed)\b'
    ]
    
    OPINION_PATTERNS = [
        r'\b(think|opinion|believe|feel|rate|rank|compare)\b',
        r'\b(best|worst|better|worse|underrated|overrated)\b',
        r'\b(should|would|could|might|analysis|tactical)\b',
        r'\b(prediction|forecast|expect|likely|probably)\b'
    ]
    
    PERSONALIZED_PATTERNS = [
        r'\b(my team|my squad|recommend|suggest|advice)\b',
        r'\b(should I|help me|what do you think I)\b',
        r'\b(for me|in my|my budget|my league)\b',
        r'\bfpl.*(recommend|suggest|advice|team|squad)\b'
    ]
    
    @classmethod
    def classify_query(cls, query: str) -> str:
        """
        Classify a query into one of the caching categories.
        
        Returns:
            'no_cache': Don't cache (personalized queries)
            'factual': Cache for 6 hours (player stats, team info)
            'news': Cache for 2 hours (recent news, transfers)
            'opinion': Cache for 24 hours (analysis, opinions)
        """
        query_lower = query.lower()
        
        # Check for personalized queries first - these should not be cached
        for pattern in cls.PERSONALIZED_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return 'no_cache'
        
        # Check for factual queries
        factual_matches = sum(1 for pattern in cls.FACTUAL_PATTERNS 
                            if re.search(pattern, query_lower, re.IGNORECASE))
        
        # Check for news queries
        news_matches = sum(1 for pattern in cls.NEWS_PATTERNS 
                         if re.search(pattern, query_lower, re.IGNORECASE))
        
        # Check for opinion queries
        opinion_matches = sum(1 for pattern in cls.OPINION_PATTERNS 
                            if re.search(pattern, query_lower, re.IGNORECASE))
        
        # Determine category based on pattern matches
        max_matches = max(factual_matches, news_matches, opinion_matches)
        
        if max_matches == 0:
            # Default to opinion category for general queries
            return 'opinion'
        elif factual_matches == max_matches:
            return 'factual'
        elif news_matches == max_matches:
            return 'news'
        else:
            return 'opinion'


class CacheStatistics:
    """Track cache performance statistics."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.total_requests = 0
        self.cache_saves = 0
        self.cache_errors = 0
        self.no_cache_requests = 0  # Track queries that aren't cached
        self.response_times = defaultdict(list)  # track by cache status
        self.query_categories = defaultdict(int)  # track by query type
        self.start_time = datetime.now()
    
    def record_hit(self, response_time: float, category: str = None):
        """Record a cache hit."""
        self.hits += 1
        self.total_requests += 1
        self.response_times['hit'].append(response_time)
        if category:
            self.query_categories[f"{category}_hit"] += 1
    
    def record_miss(self, response_time: float, category: str = None):
        """Record a cache miss."""
        self.misses += 1
        self.total_requests += 1
        self.response_times['miss'].append(response_time)
        if category:
            self.query_categories[f"{category}_miss"] += 1
    
    def record_no_cache(self, category: str = None):
        """Record a query that wasn't cached."""
        self.no_cache_requests += 1
        self.total_requests += 1
        if category:
            self.query_categories[f"{category}_no_cache"] += 1
    
    def record_save(self, category: str = None):
        """Record a successful cache save."""
        self.cache_saves += 1
        if category:
            self.query_categories[f"{category}_saved"] += 1
    
    def record_error(self):
        """Record a cache error."""
        self.cache_errors += 1
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        cacheable_requests = self.total_requests - self.no_cache_requests
        if cacheable_requests == 0:
            return 0.0
        return self.hits / cacheable_requests
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        cacheable_requests = self.total_requests - self.no_cache_requests
        if cacheable_requests == 0:
            return 0.0
        return self.misses / cacheable_requests
    
    def get_avg_response_time(self, cache_status: str) -> float:
        """Get average response time for hits or misses."""
        times = self.response_times.get(cache_status, [])
        return sum(times) / len(times) if times else 0.0
    
    def get_stats(self) -> Dict:
        """Get comprehensive cache statistics."""
        uptime = datetime.now() - self.start_time
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "no_cache_requests": self.no_cache_requests,
            "cacheable_requests": self.total_requests - self.no_cache_requests,
            "hit_rate": round(self.hit_rate, 4),
            "miss_rate": round(self.miss_rate, 4),
            "cache_saves": self.cache_saves,
            "cache_errors": self.cache_errors,
            "avg_hit_response_time": round(self.get_avg_response_time('hit'), 4),
            "avg_miss_response_time": round(self.get_avg_response_time('miss'), 4),
            "query_categories": dict(self.query_categories),
            "uptime_hours": round(uptime.total_seconds() / 3600, 2)
        }


class ResponseCacheManager:
    """Manages LLM response caching with Redis."""
    
    # TTL settings for different query types (in seconds)
    CACHE_TTL = {
        'factual': 6 * 3600,    # 6 hours for player stats, team info
        'news': 2 * 3600,       # 2 hours for recent news, transfers
        'opinion': 24 * 3600,   # 24 hours for analysis, opinions
        'no_cache': 0           # Don't cache personalized queries
    }
    
    def __init__(self, redis_client=None, default_ttl_hours: int = 24):
        self.redis = redis_client
        self.default_ttl_seconds = default_ttl_hours * 3600
        self.stats = CacheStatistics()
        self.query_classifier = QueryClassifier()
    
    def _get_ttl_for_query(self, query: str) -> tuple[int, str]:
        """Get TTL and category for a query based on its classification."""
        category = self.query_classifier.classify_query(query)
        ttl = self.CACHE_TTL.get(category, self.default_ttl_seconds)
        return ttl, category
    
    def _generate_cache_key(self, message: str, conversation_context: str = "", category: str = "") -> str:
        """Generate a cache key for the message and context."""
        # Include conversation context and category in cache key
        cache_input = f"{message}|{conversation_context}|{category}"
        return f"llm_cache_{category}:{hashlib.sha256(cache_input.encode()).hexdigest()}"
    
    def _get_conversation_context(self, memory: ConversationBufferWindowMemory) -> str:
        """Get relevant conversation context for cache key generation."""
        messages = memory.chat_memory.messages
        if not messages:
            return ""
        
        # Use last 3 messages for context (excluding current)
        recent_messages = messages[-3:] if len(messages) > 3 else messages
        context_parts = []
        
        for msg in recent_messages:
            msg_type = "H" if isinstance(msg, HumanMessage) else "A"
            # Use first 100 chars to keep cache key manageable
            content = msg.content[:100]
            context_parts.append(f"{msg_type}:{content}")
        
        return "|".join(context_parts)
    
    async def get_cached_response(self, message: str, memory: ConversationBufferWindowMemory) -> Optional[str]:
        """Get cached response if available."""
        if not self.redis:
            return None
        
        start_time = time.time()
        
        try:
            # Classify the query first
            ttl, category = self._get_ttl_for_query(message)
            
            # Don't attempt to cache personalized queries
            if category == 'no_cache':
                self.stats.record_no_cache(category)
                logger.info(f"Query classified as '{category}' - not caching: {message[:50]}...")
                return None
            
            context = self._get_conversation_context(memory)
            cache_key = self._generate_cache_key(message, context, category)
            
            cached_data = await self.redis.get(cache_key)
            response_time = time.time() - start_time
            
            if cached_data:
                self.stats.record_hit(response_time, category)
                cached_response = json.loads(cached_data)
                logger.info(f"Cache HIT ({category}) for message: {message[:50]}... (key: {cache_key[:20]}...)")
                return cached_response["response"]
            else:
                self.stats.record_miss(response_time, category)
                logger.info(f"Cache MISS ({category}) for message: {message[:50]}... (key: {cache_key[:20]}...)")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            self.stats.record_error()
            return None
    
    async def cache_response(self, message: str, response: str, memory: ConversationBufferWindowMemory):
        """Cache the LLM response with intelligent TTL based on query type."""
        if not self.redis:
            return
        
        try:
            # Classify the query and get appropriate TTL
            ttl, category = self._get_ttl_for_query(message)
            
            # Don't cache personalized queries
            if category == 'no_cache':
                logger.info(f"Not caching '{category}' query: {message[:50]}...")
                return
            
            context = self._get_conversation_context(memory)
            cache_key = self._generate_cache_key(message, context, category)
            
            cache_data = {
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "context": context,
                "category": category,
                "ttl_hours": round(ttl / 3600, 2)
            }
            
            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(cache_data)
            )
            
            self.stats.record_save(category)
            logger.info(f"Cached response ({category}, {ttl//3600}h TTL) for message: {message[:50]}... (key: {cache_key[:20]}...)")
            
        except Exception as e:
            logger.error(f"Error caching response: {e}")
            self.stats.record_error()
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics."""
        return self.stats.get_stats()


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming LLM responses."""
    
    def __init__(self, websocket=None):
        self.websocket = websocket
        self.tokens = []
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when a new token is generated."""
        if self.websocket:
            await self.websocket.send_text(json.dumps({
                "type": "token",
                "content": token,
                "timestamp": datetime.now().isoformat()
            }))
        self.tokens.append(token)


class FootballNewsSearchTool(BaseTool):
    """Tool for searching football news articles."""
    
    name: str = "football_news_search"
    description: str = """Search for football news articles using semantic search. 
    Use this when users ask about specific players, teams, transfers, injuries, or recent football news.
    Input should be a search query related to football."""
    
    session_id: str = Field(default="default")
    
    def _run(self, query: str) -> str:
        return "Use async version"
    
    async def _arun(self, query: str) -> str:
        """Search for relevant football articles."""
        try:
            session = get_session_for_tools(self.session_id)
            if not session:
                return "Database session not available"
                
            search_service = EnhancedSearchService(session)
            
            results = await search_service.enhanced_semantic_search(
                query=query,
                top_k=5,
                ranking_strategy="hybrid"
            )
            
            if not results:
                return f"No relevant articles found for: {query}"
            
            # Format results for LLM
            formatted_results = []
            for result in results[:3]:  # Limit to top 3 for context
                article = result["article_data"]
                formatted_results.append(
                    f"**{article.get('title', 'Unknown Title')}**\n"
                    f"Source: {article.get('source', 'Unknown')}\n"
                    f"Date: {article.get('published_date', 'Unknown')}\n"
                    f"Relevance: {result['final_score']:.2f}\n"
                    f"Summary: {article.get('content', '')[:200]}...\n"
                    f"URL: {article.get('url', '')}\n"
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Error in football news search: {e}")
            return f"Error searching for news: {str(e)}"


class PlayerStatsTool(BaseTool):
    """Tool for getting player statistics and information."""
    
    name: str = "player_stats"
    description: str = """Get player statistics, career information, and current status.
    Use this when users ask about specific player performance, stats, or career details.
    Input should be a player name."""
    
    session_id: str = Field(default="default")
    
    def _run(self, player_name: str) -> str:
        return "Use async version"
    
    async def _arun(self, player_name: str) -> str:
        """Get player statistics and information."""
        try:
            session = get_session_for_tools(self.session_id)
            if not session:
                return "Database session not available"
                
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            from ..models.player import Player
            from ..models.team import Team
            import aiohttp
            
            # First, search for the player in our database
            query = select(Player).options(selectinload(Player.team)).where(
                Player.name.ilike(f"%{player_name}%")
            )
            result = await session.execute(query)
            players = result.scalars().all()
            
            if not players:
                return f"Player '{player_name}' not found in database. Please check the spelling or try a different name."
            
            # If multiple players found, show options
            if len(players) > 1:
                player_list = []
                for p in players[:5]:  # Limit to 5 matches
                    team_name = p.team.name if p.team else "Unknown Team"
                    player_list.append(f"- {p.name} ({team_name}, {p.position})")
                
                return f"Multiple players found for '{player_name}':\n" + "\n".join(player_list) + "\n\nPlease be more specific with the player name."
            
            player = players[0]
            
            # Build basic player info
            team_name = player.team.name if player.team else "Unknown Team"
            player_info = [
                f"**{player.name}**",
                f"Position: {player.position or 'Unknown'}",
                f"Team: {team_name}",
                f"Status: {player.status}",
            ]
            
            if player.nationality:
                player_info.append(f"Nationality: {player.nationality}")
            
            if player.birth_date:
                from datetime import datetime
                age = datetime.now().year - player.birth_date.year
                player_info.append(f"Age: {age}")
            
            # Try to get FPL data for additional stats
            try:
                async with aiohttp.ClientSession() as http_session:
                    async with http_session.get("https://fantasy.premierleague.com/api/bootstrap-static/") as response:
                        if response.status == 200:
                            fpl_data = await response.json()
                            
                            # Find player in FPL data
                            for fpl_player in fpl_data['elements']:
                                fpl_name = f"{fpl_player['first_name']} {fpl_player['second_name']}"
                                if fpl_name.lower() == player.name.lower():
                                    player_info.extend([
                                        "",
                                        "**FPL Statistics (Current Season):**",
                                        f"Price: £{fpl_player['now_cost'] / 10}m",
                                        f"Total Points: {fpl_player['total_points']}",
                                        f"Goals: {fpl_player['goals_scored']}",
                                        f"Assists: {fpl_player['assists']}",
                                        f"Clean Sheets: {fpl_player['clean_sheets']}",
                                        f"Minutes Played: {fpl_player['minutes']}",
                                        f"Yellow Cards: {fpl_player['yellow_cards']}",
                                        f"Red Cards: {fpl_player['red_cards']}",
                                        f"Form: {fpl_player['form']}",
                                        f"Points per Game: {fpl_player['points_per_game']}",
                                    ])
                                    
                                    if fpl_player['element_type'] == 1:  # Goalkeeper
                                        player_info.extend([
                                            f"Saves: {fpl_player['saves']}",
                                            f"Goals Conceded: {fpl_player['goals_conceded']}",
                                        ])
                                    
                                    break
            except Exception as fpl_error:
                logger.warning(f"Could not fetch FPL data: {fpl_error}")
                player_info.append("\n*Note: Live FPL statistics unavailable*")
            
            # Get recent news about the player
            search_service = EnhancedSearchService(session)
            news_results = await search_service.enhanced_semantic_search(
                query=f"{player.name} {team_name}",
                top_k=3,
                ranking_strategy="temporal"
            )
            
            if news_results:
                player_info.extend([
                    "",
                    "**Recent News:**"
                ])
                for result in news_results[:2]:  # Limit to 2 recent articles
                    article = result["article_data"]
                    player_info.append(
                        f"- {article.get('title', 'Unknown Title')} "
                        f"({article.get('source', 'Unknown Source')}, "
                        f"{article.get('published_date', 'Unknown Date')})"
                    )
            
            return "\n".join(player_info)
            
        except Exception as e:
            logger.error(f"Error getting player stats: {e}")
            return f"Error retrieving player information: {str(e)}"


class FPLAnalysisTool(BaseTool):
    """Tool for Fantasy Premier League analysis and recommendations."""
    
    name: str = "fpl_analysis"
    description: str = """Analyze Fantasy Premier League prospects for players.
    Use this when users ask about FPL recommendations, player values, or fantasy football advice.
    Input should be a player name or general FPL query."""
    
    session_id: str = Field(default="default")
    
    def _run(self, query: str) -> str:
        return "Use async version"
    
    async def _arun(self, query: str) -> str:
        """Provide FPL analysis."""
        try:
            session = get_session_for_tools(self.session_id)
            if not session:
                return "Database session not available"
                
            # Search for FPL-related news and analysis
            search_service = EnhancedSearchService(session)
            
            results = await search_service.enhanced_semantic_search(
                query=f"{query} FPL fantasy premier league value price",
                top_k=3,
                ranking_strategy="hybrid"
            )
            
            fpl_info = []
            for result in results:
                article = result["article_data"]
                if "fantasy" in article.get("title", "").lower() or "fpl" in article.get("content", "").lower():
                    fpl_info.append(
                        f"FPL Analysis: {article.get('title', '')}\n"
                        f"Key points: {article.get('content', '')[:150]}...\n"
                        f"Source: {article.get('source', '')}\n"
                    )
            
            if not fpl_info:
                return f"No specific FPL analysis found for: {query}. Consider checking recent performance and injury news."
            
            return "\n".join(fpl_info)
            
        except Exception as e:
            logger.error(f"Error in FPL analysis: {e}")
            return f"Error performing FPL analysis: {str(e)}"


class LLMService:
    """Main service for LLM-powered chat functionality."""
    
    def __init__(self, session: AsyncSession, redis_client=None):
        self.session = session
        
        # Configure LangSmith tracing
        self._configure_langsmith()
        
        # Create a unique session ID and store the session
        self.session_id = str(uuid.uuid4())
        set_session_for_tools(self.session_id, session)
        
        # Initialize OpenAI LLM
        self.llm = ChatOpenAI(
            model=OPENAI_CHAT_MODEL,
            temperature=0.7,
            openai_api_key=OPENAI_API_KEY,
            streaming=True
        )
        
        # Create tools with session_id
        self.tools = [
            FootballNewsSearchTool(session_id=self.session_id),
            PlayerStatsTool(session_id=self.session_id),
            FPLAnalysisTool(session_id=self.session_id)
        ]
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Initialize conversation memory
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10  # Keep last 10 exchanges
        )
        
        # Create agent with error handling
        try:
            self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                max_iterations=3,
                early_stopping_method="generate",
                handle_parsing_errors=True
            )
            logger.info("Agent executor created successfully")
        except Exception as e:
            logger.error(f"Failed to create agent executor: {e}")
            # Fallback: create a simpler version without tools
            self.agent_executor = None
        
        # Initialize response cache manager
        self.response_cache = ResponseCacheManager(redis_client=redis_client)
    
    def _configure_langsmith(self) -> None:
        """Configure LangSmith tracing if enabled."""
        if LANGSMITH_TRACING and LANGSMITH_API_KEY:
            try:
                import os
                # Set LangSmith environment variables
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT
                os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
                os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
                
                # Add error handling for LangSmith callback issues
                os.environ["LANGCHAIN_TRACING_ERROR_ON_FAILURE"] = "false"
                
                # Disable problematic callbacks that might cause issues
                os.environ["LANGCHAIN_CALLBACKS_DISABLE"] = "true"
                
                logger.info(f"LangSmith tracing enabled for project: {LANGSMITH_PROJECT}")
            except Exception as e:
                logger.warning(f"Failed to configure LangSmith tracing: {e}")
                # Disable tracing if configuration fails
                self._disable_langsmith_tracing()
        else:
            logger.info("LangSmith tracing disabled")
            self._disable_langsmith_tracing()
    
    def _disable_langsmith_tracing(self) -> None:
        """Disable LangSmith tracing to prevent errors."""
        try:
            import os
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            os.environ["LANGCHAIN_CALLBACKS_DISABLE"] = "true"
            logger.info("LangSmith tracing disabled due to configuration issues")
        except Exception as e:
            logger.warning(f"Failed to disable LangSmith tracing: {e}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the football analysis agent."""
        return """You are a knowledgeable football analyst and expert assistant specializing in:

1. **Football News Analysis**: Provide insights on transfers, injuries, team performance, and league updates
2. **Player Analysis**: Detailed statistics, performance trends, and career analysis
3. **Fantasy Premier League (FPL)**: Strategic advice, player recommendations, and value analysis
4. **Team Performance**: Tactical analysis, form guides, and predictions

**Guidelines:**
- Always cite sources when providing specific information
- Be objective and analytical in your responses
- Provide both current news and historical context when relevant
- For FPL advice, consider value, fixtures, form, and injury status
- If you don't have recent information, be transparent about limitations
- Use the available tools to search for the most up-to-date information

**Response Style:**
- Be conversational but informative
- Use bullet points for lists and recommendations
- Include relevant statistics when available
- Provide actionable insights where possible

Remember: You have access to real-time football news and can search for specific information about players, teams, and matches."""
    
    async def chat(self, 
                   message: str, 
                   conversation_id: Optional[str] = None,
                   websocket=None) -> AsyncGenerator[str, None]:
        """
        Process a chat message and stream the response.
        
        Args:
            message: User's message
            conversation_id: Optional conversation ID for persistence
            websocket: Optional WebSocket for real-time streaming
        """
        try:
            # Classify the query first to provide context
            _, category = self.response_cache._get_ttl_for_query(message)
            
            # Check for cached response first
            cached_response = await self.response_cache.get_cached_response(message, self.memory)
            if cached_response:
                # Stream cached response with metadata
                if websocket:
                    await websocket.send_text(json.dumps({
                        "type": "cache_hit",
                        "message": f"Response retrieved from cache (category: {category})",
                        "category": category,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Simulate streaming by breaking the cached response into chunks
                    words = cached_response.split()
                    for i, word in enumerate(words):
                        chunk = word + (" " if i < len(words) - 1 else "")
                        await websocket.send_text(json.dumps({
                            "type": "token",
                            "content": chunk,
                            "timestamp": datetime.now().isoformat()
                        }))
                        # Small delay to simulate streaming
                        await asyncio.sleep(0.01)
                    
                    await websocket.send_text(json.dumps({
                        "type": "final_response",
                        "content": cached_response,
                        "timestamp": datetime.now().isoformat()
                    }))
                
                yield cached_response
                return
            
            # Cache miss or no-cache - process with LLM
            if websocket:
                if category == 'no_cache':
                    await websocket.send_text(json.dumps({
                        "type": "no_cache",
                        "message": f"Personalized query detected - not caching (category: {category})",
                        "category": category,
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
                    ttl_hours = self.response_cache.CACHE_TTL.get(category, 24) // 3600
                    await websocket.send_text(json.dumps({
                        "type": "cache_miss",
                        "message": f"Processing new request with LLM (category: {category}, will cache for {ttl_hours}h)",
                        "category": category,
                        "ttl_hours": ttl_hours,
                        "timestamp": datetime.now().isoformat()
                    }))
            
            # Set up streaming callback
            callback_handler = StreamingCallbackHandler(websocket)
            
            # Process with agent
            if self.agent_executor is None:
                # Fallback: direct LLM call without tools
                logger.warning("Agent executor not available, using direct LLM call")
                response = await self.llm.ainvoke(
                    [HumanMessage(content=message)],
                    callbacks=[callback_handler] if websocket else None
                )
                response_output = response.content
            else:
                response = await self.agent_executor.ainvoke(
                    {"input": message},
                    callbacks=[callback_handler] if websocket else None
                )
                response_output = response["output"]
            
            # Cache the response for future use
            await self.response_cache.cache_response(message, response_output, self.memory)
            
            # Stream the final response
            if websocket:
                await websocket.send_text(json.dumps({
                    "type": "final_response",
                    "content": response_output,
                    "timestamp": datetime.now().isoformat()
                }))
            
            yield response_output
            
        except Exception as e:
            logger.error(f"Error in chat processing: {e}")
            error_msg = f"I encountered an error while processing your request: {str(e)}"
            
            if websocket:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": error_msg,
                    "timestamp": datetime.now().isoformat()
                }))
            
            yield error_msg
    
    async def get_conversation_history(self, conversation_id: str) -> List[BaseMessage]:
        """Get conversation history from memory."""
        return self.memory.chat_memory.messages
    
    async def clear_conversation(self, conversation_id: str) -> None:
        """Clear conversation memory."""
        self.memory.clear()
        logger.info(f"Cleared conversation: {conversation_id}")
    
    def get_cache_statistics(self) -> Dict:
        """Get cache performance statistics."""
        return self.response_cache.get_cache_stats()
    
    def classify_query(self, query: str) -> Dict:
        """Classify a query and return its category and TTL information."""
        ttl, category = self.response_cache._get_ttl_for_query(query)
        return {
            "query": query,
            "category": category,
            "ttl_seconds": ttl,
            "ttl_hours": round(ttl / 3600, 2),
            "will_cache": category != 'no_cache'
        }
    
    async def clear_cache(self) -> Dict:
        """Clear the response cache and return final statistics."""
        if not self.response_cache.redis:
            return {"error": "No Redis client available for cache operations"}
        
        try:
            # Get final stats before clearing
            final_stats = self.get_cache_statistics()
            
            # Clear cache by pattern matching (handle both old and new cache key formats)
            patterns = ["llm_cache:*", "llm_cache_*:*"]
            cursor = 0
            keys_deleted = 0
            
            for pattern in patterns:
                cursor = 0
                while True:
                    cursor, keys = await self.response_cache.redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        await self.response_cache.redis.delete(*keys)
                        keys_deleted += len(keys)
                    if cursor == 0:
                        break
            
            logger.info(f"Cleared {keys_deleted} cache entries")
            
            # Reset statistics
            self.response_cache.stats = CacheStatistics()
            
            final_stats["keys_deleted"] = keys_deleted
            final_stats["cache_cleared_at"] = datetime.now().isoformat()
            
            return final_stats
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return {"error": f"Failed to clear cache: {str(e)}"}


# Conversation management functions
class ConversationManager:
    """Manages conversation persistence and retrieval."""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
    
    async def save_conversation(self, conversation_id: str, messages: List[BaseMessage]) -> None:
        """Save conversation to Redis."""
        if not self.redis:
            return
        
        try:
            # Serialize messages
            serialized_messages = []
            for msg in messages:
                serialized_messages.append({
                    "type": type(msg).__name__,
                    "content": msg.content,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Store in Redis with expiration (7 days)
            await self.redis.setex(
                f"conversation:{conversation_id}",
                604800,  # 7 days in seconds
                json.dumps(serialized_messages)
            )
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    async def load_conversation(self, conversation_id: str) -> List[BaseMessage]:
        """Load conversation from Redis."""
        if not self.redis:
            return []
        
        try:
            data = await self.redis.get(f"conversation:{conversation_id}")
            if not data:
                return []
            
            messages = []
            for msg_data in json.loads(data):
                if msg_data["type"] == "HumanMessage":
                    messages.append(HumanMessage(content=msg_data["content"]))
                elif msg_data["type"] == "AIMessage":
                    messages.append(AIMessage(content=msg_data["content"]))
            
            return messages
            
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")
            return []