"""
Database utility module for MongoDB operations.
"""

from typing import Dict, List
import logging
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from src.config.db_config import MONGODB_URI, DB_NAME, ARTICLES_COLLECTION

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        """Initialize database connection."""
        try:
            self.client = MongoClient(MONGODB_URI)
            self.db: Database = self.client[DB_NAME]
            self.articles: Collection = self.db[ARTICLES_COLLECTION]
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def insert_articles(self, articles: List[Dict]) -> None:
        """
        Insert articles into the database.
        
        Args:
            articles: List of article dictionaries to insert
        """
        try:
            if articles:
                # Use update_one with upsert to avoid duplicates
                for article in articles:
                    self.articles.update_one(
                        {'url': article['url']},  # Use URL as unique identifier
                        {'$set': article},
                        upsert=True
                    )
                logger.info(f"Successfully inserted {len(articles)} articles")
        except Exception as e:
            logger.error(f"Failed to insert articles: {str(e)}")
            raise
    
    def close(self) -> None:
        """Close the database connection."""
        try:
            self.client.close()
            logger.info("Closed MongoDB connection")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")
            raise 