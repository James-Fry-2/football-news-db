from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import Database
from src.db.services.vector_service import VectorService
from pydantic import BaseModel
from typing import List, Optional, Dict

router = APIRouter()

class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    source_filter: Optional[str] = None
    sentiment_filter: Optional[str] = None  # positive, negative, neutral

class SearchResult(BaseModel):
    id: str
    score: float
    title: str
    url: str
    source: str
    published_date: Optional[str]
    sentiment: Optional[float]

class ProcessingStats(BaseModel):
    pending: int
    processing: int
    completed: int
    failed: int
    total: int

async def get_db():
    async for session in Database.get_session():
        yield session

@router.post("/semantic-search", response_model=List[SearchResult])
async def semantic_search(
    request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """Perform semantic search on articles."""
    try:
        vector_service = VectorService(db)
        
        # Build filter
        filter_dict = {}
        if request.source_filter:
            filter_dict["source"] = request.source_filter
        
        if request.sentiment_filter:
            if request.sentiment_filter == "positive":
                filter_dict["sentiment"] = {"$gte": 0.1}
            elif request.sentiment_filter == "negative":
                filter_dict["sentiment"] = {"$lte": -0.1}
            elif request.sentiment_filter == "neutral":
                filter_dict["sentiment"] = {"$gte": -0.1, "$lte": 0.1}
        
        results = await vector_service.semantic_search(
            query=request.query,
            top_k=request.top_k,
            filter_dict=filter_dict if filter_dict else None
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(SearchResult(
                id=result["id"],
                score=result["score"],
                title=result["metadata"].get("title", ""),
                url=result["metadata"].get("url", ""),
                source=result["metadata"].get("source", ""),
                published_date=result["metadata"].get("published_date"),
                sentiment=result["metadata"].get("sentiment")
            ))
        
        return formatted_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processing-stats", response_model=ProcessingStats)
async def get_processing_stats(db: AsyncSession = Depends(get_db)):
    """Get vector processing statistics."""
    try:
        vector_service = VectorService(db)
        stats = await vector_service.get_processing_stats()
        return ProcessingStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reprocess/{article_id}")
async def reprocess_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Manually reprocess an article."""
    try:
        from src.tasks.vector_tasks import process_single_article_task
        task = process_single_article_task.delay(article_id)
        return {"message": f"Article {article_id} queued for reprocessing", "task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))