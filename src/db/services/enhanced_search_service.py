from typing import List, Dict, Optional, Tuple
import math
import re
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from ..models.article import Article
from .vector_service import VectorService
from ...config.search_config import SearchConfig

class EnhancedSearchService:
    """
    Advanced search service with multiple relevance scoring algorithms.
    Combines semantic similarity with various ranking factors.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.vector_service = VectorService(session)
        self.config = SearchConfig()
        
    async def enhanced_semantic_search(self,
                                     query: str,
                                     top_k: int = 20,  # Get more results for re-ranking
                                     final_k: int = 5,  # Final number to return
                                     filters: Optional[Dict] = None,
                                     ranking_strategy: str = "hybrid") -> List[Dict]:
        """
        Enhanced semantic search with multiple ranking strategies.
        
        Args:
            query: Search query
            top_k: Initial results to fetch from vector search
            final_k: Final number of results to return after re-ranking
            filters: Metadata filters for vector search
            ranking_strategy: "semantic", "hybrid", "temporal", "engagement"
        """
        
        # Step 1: Get initial semantic results
        vector_results = await self.vector_service.semantic_search(
            query=query,
            top_k=top_k,
            filter_dict=filters,
            include_scores=True
        )
        
        if not vector_results:
            return []
        
        # Step 2: Extract article IDs and get full article data
        article_ids = [int(result["id"].replace("article_", "")) for result in vector_results]
        articles_data = await self._get_articles_data(article_ids)
        
        # Step 3: Combine vector results with article data
        enhanced_results = []
        for vector_result in vector_results:
            article_id = int(vector_result["id"].replace("article_", ""))
            article_data = articles_data.get(article_id)
            
            if article_data:
                enhanced_result = {
                    **vector_result,
                    "article_data": article_data,
                    "semantic_score": vector_result["score"]
                }
                enhanced_results.append(enhanced_result)
        
        # Step 4: Apply relevance scoring based on strategy
        scored_results = await self._apply_relevance_scoring(
            enhanced_results, query, ranking_strategy
        )
        
        # Step 5: Sort by final relevance score and return top results
        scored_results.sort(key=lambda x: x["final_score"], reverse=True)
        
        return scored_results[:final_k]
    
    async def _get_articles_data(self, article_ids: List[int]) -> Dict[int, Dict]:
        """Get full article data for scoring."""
        try:
            query = select(Article).where(Article.id.in_(article_ids))
            result = await self.session.execute(query)
            articles = result.scalars().all()
            
            return {
                article.id: {
                    "id": article.id,
                    "title": article.title,
                    "content": article.content,
                    "url": article.url,
                    "source": article.source,
                    "published_date": article.published_date,
                    "sentiment_score": article.sentiment_score,
                    "created_at": article.created_at,
                    "updated_at": article.updated_at,
                    # Add any team/player relationships if available
                }
                for article in articles
            }
        except Exception as e:
            logger.error(f"Error fetching articles data: {e}")
            return {}
    
    async def _apply_relevance_scoring(self, 
                                     results: List[Dict], 
                                     query: str,
                                     strategy: str) -> List[Dict]:
        """Apply relevance scoring based on selected strategy."""
        
        if strategy == "semantic":
            return await self._semantic_only_scoring(results)
        elif strategy == "temporal":
            return await self._temporal_relevance_scoring(results, query)
        elif strategy == "engagement":
            return await self._engagement_scoring(results, query)
        elif strategy == "hybrid":
            return await self._hybrid_relevance_scoring(results, query)
        else:
            return await self._hybrid_relevance_scoring(results, query)
    
    async def _semantic_only_scoring(self, results: List[Dict]) -> List[Dict]:
        """Use only semantic similarity scores."""
        weights = self.config.SCORING_WEIGHTS["semantic_only"]
        for result in results:
            semantic_score = result["semantic_score"]
            final_score = semantic_score * weights["semantic"]
            
            result["final_score"] = final_score
            result["score_breakdown"] = {
                "semantic": semantic_score,
                "total": final_score
            }
        return results
    
    async def _temporal_relevance_scoring(self, results: List[Dict], query: str) -> List[Dict]:
        """Boost recent articles and apply time decay."""
        now = datetime.now(timezone.utc)
        
        for result in results:
            article = result["article_data"]
            semantic_score = result["semantic_score"]
            
            # Calculate time decay (newer articles get higher scores)
            if article["published_date"]:
                # Ensure both datetimes are timezone-aware for comparison
                published_date = article["published_date"]
                if published_date.tzinfo is None:
                    # If timezone-naive, assume UTC
                    published_date = published_date.replace(tzinfo=timezone.utc)
                
                days_old = (now - published_date).days
                # Exponential decay: score = base * e^(-decay_rate * days)
                time_decay = math.exp(-self.config.TEMPORAL_DECAY_RATE * days_old)
            else:
                time_decay = self.config.DEFAULT_TIME_DECAY
            
            # Text relevance boost
            text_boost = self._calculate_text_relevance_boost(query, article)
            
            # Final score combining semantic, temporal, and text relevance
            weights = self.config.SCORING_WEIGHTS["temporal"]
            final_score = (
                semantic_score * weights["semantic"] +
                time_decay * weights["temporal"] +
                text_boost * weights["text_relevance"]
            )
            
            result["final_score"] = final_score
            result["score_breakdown"] = {
                "semantic": semantic_score,
                "temporal": time_decay,
                "text_relevance": text_boost,
                "total": final_score
            }
        
        return results
    
    async def _engagement_scoring(self, results: List[Dict], query: str) -> List[Dict]:
        """Score based on source credibility and content quality signals."""
        
        for result in results:
            article = result["article_data"]
            semantic_score = result["semantic_score"]
            
            # Source credibility score
            source_score = self.config.SOURCE_WEIGHTS.get(
                article["source"], 
                self.config.DEFAULT_SOURCE_WEIGHT
            )
            
            # Content quality indicators
            content_quality = self._calculate_content_quality_score(article)
            
            # Text relevance
            text_boost = self._calculate_text_relevance_boost(query, article)
            
            # Sentiment relevance (neutral to positive articles might be more valuable)
            sentiment_boost = self._calculate_sentiment_relevance(article)
            
            # Combined score
            weights = self.config.SCORING_WEIGHTS["engagement"]
            final_score = (
                semantic_score * weights["semantic"] +
                source_score * weights["source_credibility"] +
                content_quality * weights["content_quality"] +
                text_boost * weights["text_relevance"] +
                sentiment_boost * weights["sentiment"]
            )
            
            result["final_score"] = final_score
            result["score_breakdown"] = {
                "semantic": semantic_score,
                "source_credibility": source_score,
                "content_quality": content_quality,
                "text_relevance": text_boost,
                "sentiment": sentiment_boost,
                "total": final_score
            }
        
        return results
    
    async def _hybrid_relevance_scoring(self, results: List[Dict], query: str) -> List[Dict]:
        """Advanced hybrid scoring combining multiple factors."""
        now = datetime.now(timezone.utc)
        
        for result in results:
            article = result["article_data"]
            semantic_score = result["semantic_score"]
            
            # 1. Temporal relevance (exponential decay)
            if article["published_date"]:
                # Ensure both datetimes are timezone-aware for comparison
                published_date = article["published_date"]
                if published_date.tzinfo is None:
                    # If timezone-naive, assume UTC
                    published_date = published_date.replace(tzinfo=timezone.utc)
                
                days_old = (now - published_date).days
                time_decay = math.exp(-self.config.HYBRID_DECAY_RATE * days_old)
            else:
                time_decay = self.config.DEFAULT_TIME_DECAY
            
            # 2. Source credibility
            source_score = self.config.SOURCE_WEIGHTS.get(
                article["source"], 
                self.config.DEFAULT_SOURCE_WEIGHT
            )
            
            # 3. Text relevance boost
            text_boost = self._calculate_text_relevance_boost(query, article)
            
            # 4. Content quality
            content_quality = self._calculate_content_quality_score(article)
            
            # 5. Sentiment relevance
            sentiment_boost = self._calculate_sentiment_relevance(article)
            
            # Hybrid scoring formula
            weights = self.config.SCORING_WEIGHTS["hybrid"]
            final_score = (
                semantic_score * weights["semantic"] +
                time_decay * weights["temporal"] +
                source_score * weights["source_credibility"] +
                text_boost * weights["text_relevance"] +
                content_quality * weights["content_quality"] +
                sentiment_boost * weights["sentiment"]
            )
            
            result["final_score"] = final_score
            result["score_breakdown"] = {
                "semantic": semantic_score,
                "temporal": time_decay,
                "source_credibility": source_score,
                "text_relevance": text_boost,
                "content_quality": content_quality,
                "sentiment": sentiment_boost,
                "total": final_score
            }
        
        return results
    
    def _calculate_text_relevance_boost(self, query: str, article: Dict) -> float:
        """Calculate boost based on exact text matches in title/content."""
        query_terms = set(query.lower().split())
        title_text = (article.get("title") or "").lower()
        content_text = (article.get("content") or "").lower()
        
        # Count matches in title (weighted higher)
        title_matches = sum(1 for term in query_terms if term in title_text)
        title_boost = (title_matches / len(query_terms)) * self.config.TITLE_MATCH_WEIGHT
        
        # Count matches in content
        content_matches = sum(1 for term in query_terms if term in content_text)
        content_boost = content_matches / len(query_terms)
        
        # Combine and normalize
        total_boost = min(title_boost + content_boost, 1.0)
        return total_boost
    
    def _calculate_content_quality_score(self, article: Dict) -> float:
        """Estimate content quality based on various signals."""
        content = article.get("content", "")
        title = article.get("title", "")
        
        # Content length (sweet spot around configured range)
        content_length = len(content)
        min_len = self.config.OPTIMAL_CONTENT_LENGTH_MIN
        max_len = self.config.OPTIMAL_CONTENT_LENGTH_MAX
        
        if min_len <= content_length <= max_len:
            length_score = 1.0
        elif content_length < min_len:
            length_score = content_length / min_len
        else:
            length_score = max(0.5, max_len / content_length)
        
        # Title quality (reasonable length, not clickbait indicators)
        title_length = len(title)
        title_score = 1.0
        if (title_length < self.config.MIN_TITLE_LENGTH or 
            title_length > self.config.MAX_TITLE_LENGTH):
            title_score = 0.8
        
        # Check for clickbait patterns (lower score)
        for pattern in self.config.CLICKBAIT_PATTERNS:
            if re.search(pattern, title.lower()):
                title_score *= self.config.CLICKBAIT_PENALTY
                break
        
        return (length_score + title_score) / 2.0
    
    def _calculate_sentiment_relevance(self, article: Dict) -> float:
        """Calculate relevance boost based on sentiment."""
        sentiment_score = article.get("sentiment_score", 0.0)
        
        if sentiment_score is None:
            return self.config.NEUTRAL_SENTIMENT_BASE
        
        # Slightly favor neutral to positive articles
        if sentiment_score >= 0:
            return (self.config.NEUTRAL_SENTIMENT_BASE + 
                   (sentiment_score * self.config.POSITIVE_SENTIMENT_MULTIPLIER))
        else:
            return (self.config.NEUTRAL_SENTIMENT_BASE + 
                   (sentiment_score * self.config.NEGATIVE_SENTIMENT_MULTIPLIER))