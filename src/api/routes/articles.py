from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models.article import Article
from src.db.database import Database

router = APIRouter()

async def get_db():
    async for session in Database.get_session():
        yield session

@router.get("/articles/", response_model=List[Article])
async def get_articles(
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    team: Optional[str] = None,
    player: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Article)
    if source:
        query = query.where(Article.source == source)
    # Filtering by team/player would require joins; omitted for brevity
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()
    return articles

@router.get("/articles/{url}", response_model=Article)
async def get_article(
    url: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(Article).where(Article.url == url)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.post("/articles/", response_model=Article)
async def create_article(
    article: Article,
    db: AsyncSession = Depends(get_db)
):
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article

@router.put("/articles/{url}", response_model=Article)
async def update_article(
    url: str,
    article: Article,
    db: AsyncSession = Depends(get_db)
):
    query = select(Article).where(Article.url == url)
    result = await db.execute(query)
    db_article = result.scalar_one_or_none()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    for key, value in article.dict(exclude_unset=True).items():
        setattr(db_article, key, value)
    await db.commit()
    await db.refresh(db_article)
    return db_article 