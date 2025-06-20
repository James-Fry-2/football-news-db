from typing import List, Dict, Optional, Tuple
import math
import re
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from ..models.article import Article
from .vector_service import VectorService

class EnhancedSearchService:
    """
    Advanced search service with multiple relevance scoring algorithms.
    Combines semantic similarity with various ranking factors.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.vector_service = VectorService(session)
        
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
        for result in results:
            result["final_score"] = result["semantic_score"]
            result["score_breakdown"] = {
                "semantic": result["semantic_score"],
                "total": result["semantic_score"]
            }
        return results
    
    async def _temporal_relevance_scoring(self, results: List[Dict], query: str) -> List[Dict]:
        """Boost recent articles and apply time decay."""
        now = datetime.utcnow()
        
        for result in results:
            article = result["article_data"]
            semantic_score = result["semantic_score"]
            
            # Calculate time decay (newer articles get higher scores)
            if article["published_date"]:
                days_old = (now - article["published_date"]).days
                # Exponential decay: score = base * e^(-decay_rate * days)
                time_decay = math.exp(-0.1 * days_old)  # Decay rate of 0.1
            else:
                time_decay = 0.5  # Default for articles without dates
            
            # Text relevance boost
            text_boost = self._calculate_text_relevance_boost(query, article)
            
            # Final score combining semantic, temporal, and text relevance
            final_score = (
                semantic_score * 0.6 +          # 60% semantic similarity
                time_decay * 0.3 +              # 30% temporal relevance
                text_boost * 0.1                # 10% text matching
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
        
        # Source credibility weights
        source_weights = {
            "BBC Sport": 1.0,
            "Sky Sports": 0.95,
            "Guardian": 0.95,
            "Telegraph": 0.9,
            "Fantasy Football Scout": 0.85,
            "ESPN": 0.8,
        }
        
        for result in results:
            article = result["article_data"]
            semantic_score = result["semantic_score"]
            
            # Source credibility score
            source_score = source_weights.get(article["source"], 0.7)
            
            # Content quality indicators
            content_quality = self._calculate_content_quality_score(article)
            
            # Text relevance
            text_boost = self._calculate_text_relevance_boost(query, article)
            
            # Sentiment relevance (neutral to positive articles might be more valuable)
            sentiment_boost = self._calculate_sentiment_relevance(article)
            
            # Combined score
            final_score = (
                semantic_score * 0.5 +          # 50% semantic similarity
                source_score * 0.2 +            # 20% source credibility
                content_quality * 0.15 +        # 15% content quality
                text_boost * 0.1 +              # 10% text matching
                sentiment_boost * 0.05          # 5% sentiment relevance
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
        now = datetime.utcnow()
        
        # Source credibility weights
        source_weights = {
            "BBC Sport": 1.0,
            "Sky Sports": 0.95,
            "Guardian": 0.95,
            "Telegraph": 0.9,
            "Fantasy Football Scout": 0.85,
            "ESPN": 0.8,
        }
        
        for result in results:
            article = result["article_data"]
            semantic_score = result["semantic_score"]
            
            # 1. Temporal relevance (exponential decay)
            if article["published_date"]:
                days_old = (now - article["published_date"]).days
                time_decay = math.exp(-0.05 * days_old)  # Slower decay for hybrid
            else:
                time_decay = 0.5
            
            # 2. Source credibility
            source_score = source_weights.get(article["source"], 0.7)
            
            # 3. Text relevance boost
            text_boost = self._calculate_text_relevance_boost(query, article)
            
            # 4. Content quality
            content_quality = self._calculate_content_quality_score(article)
            
            # 5. Sentiment relevance
            sentiment_boost = self._calculate_sentiment_relevance(article)
            
            # Hybrid scoring formula
            final_score = (
                semantic_score * 0.4 +          # 40% semantic similarity
                time_decay * 0.25 +             # 25% temporal relevance
                source_score * 0.15 +           # 15% source credibility
                text_boost * 0.1 +              # 10% text matching
                content_quality * 0.07 +        # 7% content quality
                sentiment_boost * 0.03          # 3% sentiment relevance
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
        title_boost = (title_matches / len(query_terms)) * 2.0  # 2x weight for title
        
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
        
        # Content length (sweet spot around 500-2000 chars)
        content_length = len(content)
        if 500 <= content_length <= 2000:
            length_score = 1.0
        elif content_length < 500:
            length_score = content_length / 500.0
        else:
            length_score = max(0.5, 2000 / content_length)
        
        # Title quality (reasonable length, not clickbait indicators)
        title_length = len(title)
        title_score = 1.0
        if title_length < 20 or title_length > 150:
            title_score = 0.8
        
        # Check for clickbait patterns (lower score)
        clickbait_patterns = [
            r"\d+\s+(things|ways|reasons|facts)",
            r"you won't believe",
            r"shocking",
            r"amazing",
            r"incredible"
        ]
        for pattern in clickbait_patterns:
            if re.search(pattern, title.lower()):
                title_score *= 0.7
                break
        
        return (length_score + title_score) / 2.0
    
    def _calculate_sentiment_relevance(self, article: Dict) -> float:
        """Calculate relevance boost based on sentiment."""
        sentiment_score = article.get("sentiment_score", 0.0)
        
        if sentiment_score is None:
            return 0.5  # Neutral default
        
        # Slightly favor neutral to positive articles
        if sentiment_score >= 0:
            return 0.5 + (sentiment_score * 0.3)  # 0.5 to 0.8 range
        else:
            return 0.5 + (sentiment_score * 0.2)  # 0.3 to 0.5 range