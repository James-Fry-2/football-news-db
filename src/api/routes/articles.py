from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...db.models.article import Article
from ...db.services.article_service import ArticleService
from ..dependencies import get_database

router = APIRouter()

@router.get("/articles/", response_model=List[Article])
async def get_articles(
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    team: Optional[str] = None,
    player: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get articles with optional filtering.
    """
    article_service = ArticleService(db)
    articles = await article_service.get_articles(
        skip=skip,
        limit=limit,
        source=source,
        team=team,
        player=player
    )
    return articles

@router.get("/articles/{url}", response_model=Article)
async def get_article(
    url: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get a specific article by URL.
    """
    article_service = ArticleService(db)
    article = await article_service.get_articles(url=url)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.post("/articles/", response_model=Article)
async def create_article(
    article: Article,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new article.
    """
    article_service = ArticleService(db)
    saved_article = await article_service.save_article(article.dict())
    if not saved_article:
        raise HTTPException(status_code=400, detail="Article already exists")
    return saved_article

@router.put("/articles/{url}", response_model=Article)
async def update_article(
    url: str,
    article: Article,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update an existing article.
    """
    article_service = ArticleService(db)
    updated_article = await article_service.update_article(url, article.dict())
    if not updated_article:
        raise HTTPException(status_code=404, detail="Article not found")
    return updated_article 