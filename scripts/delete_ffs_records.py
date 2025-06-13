#!/usr/bin/env python3
"""
Script to delete all Fantasy Football Scout records from the database.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import select, delete
from loguru import logger
from src.db.database import Database
from src.db.models.article import Article

async def delete_ffs_records():
    """Delete all Fantasy Football Scout records from the database."""
    try:
        # Connect to database
        await Database.connect_db()
        
        async with Database.get_session() as session:
            # First, count how many FFS articles exist
            count_query = select(Article).where(Article.source == 'Fantasy Football Scout')
            result = await session.execute(count_query)
            articles = result.scalars().all()
            article_count = len(articles)
            
            if article_count == 0:
                logger.info("No Fantasy Football Scout articles found in database")
                return
                
            logger.info(f"Found {article_count} Fantasy Football Scout articles to delete")
            
            # Ask for confirmation
            response = input(f"Are you sure you want to delete {article_count} Fantasy Football Scout articles? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                logger.info("Operation cancelled")
                return
                
            # Delete all FFS articles
            delete_query = delete(Article).where(Article.source == 'Fantasy Football Scout')
            result = await session.execute(delete_query)
            await session.commit()
            
            deleted_count = result.rowcount
            logger.success(f"Successfully deleted {deleted_count} Fantasy Football Scout articles")
            
    except Exception as e:
        logger.error(f"Error deleting FFS records: {e}")
        raise
    finally:
        await Database.close_db()

if __name__ == "__main__":
    asyncio.run(delete_ffs_records()) 