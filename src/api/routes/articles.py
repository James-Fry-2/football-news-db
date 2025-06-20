from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models.article import Article as ArticleModel
from src.db.database import Database
from src.api.schemas import Article, ArticleCreate, ArticleUpdate

router = APIRouter()

async def get_db():
    async with Database.get_session() as session:
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

@router.get("/id/{article_id}/content")
async def get_article_content(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Extract article content by ID"""
    try:
        query = select(ArticleModel.content, ArticleModel.title, ArticleModel.url, ArticleModel.source, ArticleModel.published_date).where(
            ArticleModel.id == article_id,
            ArticleModel.is_deleted == False,
            ArticleModel.status == 'active'
        )
        result = await db.execute(query)
        article_data = result.first()
        
        if not article_data:
            raise HTTPException(status_code=404, detail=f"Article with ID {article_id} not found or not active")
        
        return {
            "id": article_id,
            "content": article_data.content,
            "title": article_data.title,
            "url": str(article_data.url),
            "source": article_data.source,
            "published_date": article_data.published_date
        }
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid article ID format. Must be an integer.")

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