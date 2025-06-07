#!/usr/bin/env python
"""
Script to run a crawler and upload data to PostgreSQL.
Usage: python run_crawler.py [crawler_name] [--limit N]
"""

import argparse
import logging
import sys
import asyncio
from typing import List, Dict

from src.crawlers import BBCCrawler, FFSCrawler
from src.db.database import Database
from src.db.services.article_service import ArticleService
from src.config.db_config import DATABASE_URL
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Map of crawler names to crawler classes
CRAWLERS = {
    'bbc': BBCCrawler,
    'ffs': FFSCrawler,
}

async def run_crawler(crawler_name: str, limit: int = None) -> List[Dict]:
    """
    Run a crawler and return the collected articles.
    
    Args:
        crawler_name: Name of the crawler to run
        limit: Maximum number of articles to collect (None for no limit)
        
    Returns:
        List of article dictionaries
    """
    if crawler_name not in CRAWLERS:
        logger.error(f"Unknown crawler: {crawler_name}")
        logger.info(f"Available crawlers: {', '.join(CRAWLERS.keys())}")
        return []
    
    # Connect to database
    await Database.connect_db(DATABASE_URL)
    
    try:
        # Create database session
        async with Database.get_session() as session:
            # Create article service
            article_service = ArticleService(session)
            
            # Create crawler instance with database services
            crawler_class = CRAWLERS[crawler_name]
            crawler = crawler_class(article_service, session)
            
            logger.info(f"Running {crawler_name} crawler...")
            
            # Use fetch_articles method (database-driven)
            articles = await crawler.fetch_articles()
            
            if limit and limit > 0:
                articles = articles[:limit]
                logger.info(f"Limited to {limit} articles")
            
            logger.info(f"Collected {len(articles)} articles")
            
            # Save articles to database
            if articles:
                logger.info(f"Saving {len(articles)} articles to database...")
                saved_count = 0
                for article in articles:
                    result = await article_service.save_article(article)
                    if result:
                        saved_count += 1
                logger.info(f"Successfully saved {saved_count} articles to database")
            
            return articles
            
    finally:
        await Database.close_db()

async def main():
    """Main function to parse arguments and run the crawler."""
    parser = argparse.ArgumentParser(description="Run a crawler and save data to PostgreSQL")
    parser.add_argument("crawler", help="Name of the crawler to run")
    parser.add_argument("--limit", type=int, help="Maximum number of articles to collect")
    
    args = parser.parse_args()
    
    # Run the crawler (it will automatically save to database)
    articles = await run_crawler(args.crawler, args.limit)
    
    logger.info(f"Process completed. {len(articles)} articles processed.")

if __name__ == "__main__":
    asyncio.run(main()) 