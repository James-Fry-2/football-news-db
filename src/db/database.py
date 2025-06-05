from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from loguru import logger
from typing import AsyncGenerator

Base = declarative_base()

class Database:
    engine = None
    async_session = None

    @classmethod
    async def connect_db(cls, database_url: str):
        try:
            # Convert the URL to async format if it's not already
            if not database_url.startswith('postgresql+asyncpg://'):
                database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
            
            cls.engine = create_async_engine(
                database_url,
                echo=False,  # Set to True for SQL query logging
                future=True,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600    # Recycle connections every hour
            )
            
            cls.async_session = sessionmaker(
                cls.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("Connected to PostgreSQL database.")
        except Exception as e:
            logger.error(f"Could not connect to PostgreSQL: {e}")
            raise

    @classmethod
    async def close_db(cls):
        if cls.engine:
            await cls.engine.dispose()
            logger.info("Closed PostgreSQL connection.")

    @classmethod
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        if not cls.async_session:
            raise Exception("Database not initialized. Call connect_db first.")
        async with cls.async_session() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @classmethod
    async def init_db(cls):
        """Initialize the database by creating all tables."""
        # Import models to ensure they're registered with Base
        from .models import Article, Team, Player
        
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully.")