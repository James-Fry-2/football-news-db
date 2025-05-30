from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models.article import Article as ArticleModel
from src.db.database import Database
from src.api.schemas import Article, ArticleCreate, ArticleUpdate

router = APIRouter()

async def get_db():
    async for session in Database.get_session():
        yield session

@router.get("/", response_model=List[Article])
async def get_articles(
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    team: Optional[str] = None,
    player: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(ArticleModel)
    if source:
        query = query.where(ArticleModel.source == source)
    # Filtering by team/player would require joins; omitted for brevity
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()
    return articles

@router.get("/{url}", response_model=Article)
async def get_article(
    url: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(ArticleModel).where(ArticleModel.url == url)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.post("/", response_model=Article)
async def create_article(
    article: ArticleCreate,
    db: AsyncSession = Depends(get_db)
):
    db_article = ArticleModel(**article.model_dump())
    db.add(db_article)
    await db.commit()
    await db.refresh(db_article)
    return db_article

@router.put("/{url}", response_model=Article)
async def update_article(
    url: str,
    article: ArticleUpdate,
    db: AsyncSession = Depends(get_db)
):
    query = select(ArticleModel).where(ArticleModel.url == url)
    result = await db.execute(query)
    db_article = result.scalar_one_or_none()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    update_data = article.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_article, key, value)
    
    await db.commit()
    await db.refresh(db_article)
    return db_article 