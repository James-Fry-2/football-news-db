"""
Database connection and session management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

Base = declarative_base()

class Database:
    """Database connection manager."""
    
    engine = None
    async_session = None
    
    @classmethod
    async def connect_db(cls, database_url: str):
        """Connect to the database."""
        try:
            cls.engine = create_async_engine(
                database_url,
                echo=False,
                future=True,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            cls.async_session = async_sessionmaker(
                cls.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )
            logger.info("Connected to PostgreSQL database.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    @classmethod
    @asynccontextmanager
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if not cls.async_session:
            raise RuntimeError("Database not initialized. Call connect_db first.")
        
        session = cls.async_session()
        try:
            yield session
        finally:
            await session.close()
    
    @classmethod
    async def init_db(cls):
        """Initialize database tables."""
        if not cls.engine:
            raise RuntimeError("Database not initialized. Call connect_db first.")
        
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully.")
    
    @classmethod
    async def drop_all_tables(cls):
        """Drop all database tables."""
        if not cls.engine:
            raise RuntimeError("Database not initialized. Call connect_db first.")
        
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("All database tables dropped successfully.")
    
    @classmethod
    async def close_db(cls):
        """Close database connection."""
        if cls.engine:
            await cls.engine.dispose()
            logger.info("Closed PostgreSQL connection.")