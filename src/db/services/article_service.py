from typing import List, Optional, Dict
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from ..models.article import Article
from ..models.player import Player
from ..models.team import Team

class ArticleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_duplicate(self, url: str) -> bool:
        query = select(Article).where(Article.url == url)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def save_article(self, article_data: Dict) -> Optional[Article]:
        try:
            if await self.is_duplicate(article_data["url"]):
                logger.info(f"Duplicate article found: {article_data['url']}")
                return None
            article = Article(**article_data)
            self.session.add(article)
            await self.session.commit()
            await self.session.refresh(article)
            logger.info(f"Saved new article: {article.title}")
            return article
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error saving article: {e}")
            return None

    async def get_articles(
        self,
        skip: int = 0,
        limit: int = 10,
        source: Optional[str] = None,
        team: Optional[str] = None,
        player: Optional[str] = None
    ) -> List[Article]:
        query = select(Article)
        if source:
            query = query.where(Article.source == source)
        # Filtering by team/player would require joins
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_article_by_url(self, url: str) -> Optional[Article]:
        query = select(Article).where(Article.url == url)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_article(self, url: str, article_data: Dict) -> Optional[Article]:
        query = select(Article).where(Article.url == url)
        result = await self.session.execute(query)
        db_article = result.scalar_one_or_none()
        if not db_article:
            return None
        for key, value in article_data.items():
            setattr(db_article, key, value)
        db_article.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(db_article)
        return db_article

    async def delete_article(self, url: str) -> bool:
        query = select(Article).where(Article.url == url)
        result = await self.session.execute(query)
        db_article = result.scalar_one_or_none()
        if not db_article:
            return False
        await self.session.delete(db_article)
        await self.session.commit()
        return True 