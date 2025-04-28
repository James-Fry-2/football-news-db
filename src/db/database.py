from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    @classmethod
    async def connect_db(cls, mongodb_url: str):
        try:
            cls.client = AsyncIOMotorClient(mongodb_url)
            cls.db = cls.client.football_news
            logger.info("Connected to MongoDB.")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise

    @classmethod
    async def close_db(cls):
        if cls.client:
            cls.client.close()
            logger.info("Closed MongoDB connection.")

    @classmethod
    def get_db(cls):
        if not cls.db:
            raise Exception("Database not initialized. Call connect_db first.")
        return cls.db 