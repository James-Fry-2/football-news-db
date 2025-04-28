from typing import List, Optional, Dict
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from loguru import logger
from bson import ObjectId

from ..models.article import Article

class ArticleService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.articles

    async def create_indexes(self):
        """Create necessary indexes for article collection."""
        await self.collection.create_index("url", unique=True)
        await self.collection.create_index("title")
        await self.collection.create_index("published_date")

    async def is_duplicate(self, url: str) -> bool:
        """
        Check if an article with the given URL already exists.
        
        Args:
            url: The URL of the article to check
            
        Returns:
            bool: True if the article exists, False otherwise
        """
        try:
            article = await self.collection.find_one({"url": url})
            return article is not None
        except Exception as e:
            logger.error(f"Error checking for duplicate article: {e}")
            return False

    async def save_article(self, article_data: Dict) -> Optional[Article]:
        """
        Save an article to the database if it doesn't already exist.
        
        Args:
            article_data: Dictionary containing article data
            
        Returns:
            Article: The saved article or None if it was a duplicate
        """
        try:
            # Check if article already exists
            if await self.is_duplicate(article_data["url"]):
                logger.info(f"Duplicate article found: {article_data['url']}")
                return None

            # Create Article instance
            article = Article(**article_data)
            
            # Insert into database
            await self.collection.insert_one(article.dict())
            logger.info(f"Saved new article: {article.title}")
            
            return article
            
        except Exception as e:
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
        query = {}
        if source:
            query["source"] = source
        if team:
            query["teams"] = team
        if player:
            query["players"] = player

        cursor = self.collection.find(query).skip(skip).limit(limit)
        articles = await cursor.to_list(length=limit)
        return [Article(**article) for article in articles]

    async def get_article_by_url(self, url: str) -> Optional[Article]:
        article = await self.collection.find_one({"url": url})
        return Article(**article) if article else None

    async def create_article(self, article: Article) -> Article:
        article_dict = article.dict()
        article_dict["created_at"] = datetime.utcnow()
        article_dict["updated_at"] = datetime.utcnow()
        
        await self.collection.insert_one(article_dict)
        return article

    async def update_article(self, url: str, article: Article) -> Optional[Article]:
        article_dict = article.dict(exclude_unset=True)
        article_dict["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"url": url},
            {"$set": article_dict}
        )
        
        if result.modified_count:
            return await self.get_article_by_url(url)
        return None

    async def delete_article(self, url: str) -> bool:
        result = await self.collection.delete_one({"url": url})
        return result.deleted_count > 0 