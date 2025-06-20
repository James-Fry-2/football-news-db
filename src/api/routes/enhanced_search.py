from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime

from ...db.database import Database
from ...db.services.enhanced_search_service import EnhancedSearchService

router = APIRouter()

class EnhancedSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, ge=1, le=50, description="Number of results to return")
    ranking_strategy: Literal["semantic", "hybrid", "temporal", "engagement"] = Field(
        "hybrid", description="Ranking algorithm to use"
    )
    filters: Optional[Dict] = Field(None, description="Metadata filters")
    
    # Advanced filtering options
    source_filter: Optional[str] = Field(None, description="Filter by news source")
    date_from: Optional[datetime] = Field(None, description="Filter articles from this date")
    date_to: Optional[datetime] = Field(None, description="Filter articles to this date")
    sentiment_filter: Optional[Literal["positive", "negative", "neutral"]] = Field(
        None, description="Filter by sentiment"
    )
    min_relevance_score: Optional[float] = Field(
        0.0, ge=0.0, le=1.0, description="Minimum relevance score threshold"
    )

class ScoreBreakdown(BaseModel):
    semantic: float = Field(..., description="Semantic similarity score")
    temporal: Optional[float] = Field(None, description="Temporal relevance score")
    source_credibility: Optional[float] = Field(None, description="Source credibility score")
    text_relevance: Optional[float] = Field(None, description="Text matching score")
    content_quality: Optional[float] = Field(None, description="Content quality score")
    sentiment: Optional[float] = Field(None, description="Sentiment relevance score")
    total: float = Field(..., description="Final combined score")

class EnhancedSearchResult(BaseModel):
    id: str
    article_id: int
    title: str
    url: str
    source: str
    published_date: Optional[datetime]
    content_snippet: str = Field(..., description="First 200 chars of content")
    
    # Scoring information
    final_score: float = Field(..., description="Final relevance score")
    score_breakdown: ScoreBreakdown
    
    # Metadata
    sentiment_score: Optional[float]
    created_at: datetime
    
    # Ranking information
    rank: int = Field(..., description="Result ranking (1-based)")

class SearchResponse(BaseModel):
    query: str
    total_results: int
    ranking_strategy: str
    results: List[EnhancedSearchResult]
    
    # Performance metrics
    search_time_ms: float
    filters_applied: Dict

class SearchSuggestion(BaseModel):
    """Search suggestions based on query analysis."""
    suggested_queries: List[str]
    related_teams: List[str]
    related_players: List[str]

async def get_db():
    async with Database.get_session() as session:
        yield session

@router.post("/enhanced-search", response_model=SearchResponse)
async def enhanced_semantic_search(
    request: EnhancedSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Enhanced semantic search with advanced relevance scoring.
    
    Supports multiple ranking strategies:
    - semantic: Pure vector similarity
    - temporal: Boosts recent articles
    - engagement: Considers source credibility and content quality
    - hybrid: Combines all factors (recommended)
    """
    import time
    start_time = time.time()
    
    try:
        search_service = EnhancedSearchService(db)
        
        # Build filters
        filters = request.filters or {}
        
        if request.source_filter:
            filters["source"] = request.source_filter
        
        if request.sentiment_filter:
            if request.sentiment_filter == "positive":
                filters["sentiment"] = {"$gte": 0.1}
            elif request.sentiment_filter == "negative":
                filters["sentiment"] = {"$lte": -0.1}
            elif request.sentiment_filter == "neutral":
                filters["sentiment"] = {"$gte": -0.1, "$lte": 0.1}
        
        # Date filtering (if supported by Pinecone metadata)
        if request.date_from:
            filters["published_date"] = filters.get("published_date", {})
            filters["published_date"]["$gte"] = request.date_from.isoformat()
        
        if request.date_to:
            filters["published_date"] = filters.get("published_date", {})
            filters["published_date"]["$lte"] = request.date_to.isoformat()
        
        # Perform enhanced search
        results = await search_service.enhanced_semantic_search(
            query=request.query,
            top_k=min(request.top_k * 2, 50),  # Get extra results for filtering
            final_k=request.top_k,
            filters=filters if filters else None,
            ranking_strategy=request.ranking_strategy
        )
        
        # Apply minimum relevance score filter
        if request.min_relevance_score > 0:
            results = [r for r in results if r["final_score"] >= request.min_relevance_score]
        
        # Format results
        formatted_results = []
        for idx, result in enumerate(results[:request.top_k], 1):
            article = result["article_data"]
            content_snippet = (article.get("content", "") or "")[:200]
            if len(content_snippet) == 200:
                content_snippet += "..."
            
            formatted_result = EnhancedSearchResult(
                id=result["id"],
                article_id=article["id"],
                title=article.get("title", ""),
                url=article.get("url", ""),
                source=article.get("source", ""),
                published_date=article.get("published_date"),
                content_snippet=content_snippet,
                final_score=result["final_score"],
                score_breakdown=ScoreBreakdown(**result["score_breakdown"]),
                sentiment_score=article.get("sentiment_score"),
                created_at=article.get("created_at"),
                rank=idx
            )
            formatted_results.append(formatted_result)
        
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return SearchResponse(
            query=request.query,
            total_results=len(formatted_results),
            ranking_strategy=request.ranking_strategy,
            results=formatted_results,
            search_time_ms=round(search_time, 2),
            filters_applied=filters
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.get("/search-suggestions")
async def get_search_suggestions(
    query: str = Query(..., description="Partial query for suggestions"),
    db: AsyncSession = Depends(get_db)
) -> SearchSuggestion:
    """
    Get search suggestions based on query analysis.
    Analyzes the query to suggest related teams, players, and alternative queries.
    """
    try:
        #TODO: This would integrate with your team/player data
        # For now, return mock suggestions
        
        query_lower = query.lower()
        
        # Sample team suggestions (replace with actual team lookup)
        all_teams = [
            "Manchester United", "Manchester City", "Liverpool", "Chelsea", 
            "Arsenal", "Tottenham", "Newcastle", "Brighton", "Aston Villa"
        ]
        related_teams = [team for team in all_teams if any(word in team.lower() for word in query_lower.split())]
        
        # Sample player suggestions (replace with actual player lookup)
        suggested_players = []
        if "transfer" in query_lower:
            suggested_players = ["Erling Haaland", "Mohamed Salah", "Declan Rice"]
        
        # Generate query suggestions
        suggested_queries = [
            f"{query} transfer news",
            f"{query} latest news",
            f"{query} injury update",
            f"{query} match report"
        ]
        
        return SearchSuggestion(
            suggested_queries=suggested_queries[:3],
            related_teams=related_teams[:5],
            related_players=suggested_players[:5]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestion error: {str(e)}")

@router.get("/ranking-strategies")
async def get_ranking_strategies():
    """Get information about available ranking strategies."""
    return {
        "strategies": {
            "semantic": {
                "name": "Semantic Only",
                "description": "Pure vector similarity based on content meaning",
                "best_for": "Finding articles with similar topics and themes",
                "weights": {"semantic_similarity": 1.0}
            },
            "temporal": {
                "name": "Temporal Relevance",
                "description": "Boosts recent articles with time decay",
                "best_for": "Finding recent news and breaking stories",
                "weights": {
                    "semantic_similarity": 0.6,
                    "temporal_relevance": 0.3,
                    "text_matching": 0.1
                }
            },
            "engagement": {
                "name": "Engagement Quality",
                "description": "Considers source credibility and content quality",
                "best_for": "Finding high-quality, credible articles",
                "weights": {
                    "semantic_similarity": 0.5,
                    "source_credibility": 0.2,
                    "content_quality": 0.15,
                    "text_matching": 0.1,
                    "sentiment": 0.05
                }
            },
            "hybrid": {
                "name": "Hybrid Scoring",
                "description": "Combines all ranking factors for balanced results",
                "best_for": "General search with balanced relevance",
                "weights": {
                    "semantic_similarity": 0.4,
                    "temporal_relevance": 0.25,
                    "source_credibility": 0.15,
                    "text_matching": 0.1,
                    "content_quality": 0.07,
                    "sentiment": 0.03
                }
            }
        },
        "default_strategy": "hybrid",
        "recommended_use_cases": {
            "breaking_news": "temporal",
            "research": "engagement", 
            "general_search": "hybrid",
            "topic_exploration": "semantic"
        }
    }