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
from src.utils.db import DatabaseManager

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

def run_crawler(crawler_name: str, limit: int = None) -> List[Dict]:
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
    
    crawler_class = CRAWLERS[crawler_name]
    logger.info(f"Running {crawler_name} crawler...")
    
    crawler = crawler_class()
    articles = crawler.crawl()
    
    if limit and limit > 0:
        articles = articles[:limit]
        logger.info(f"Limited to {limit} articles")
    
    logger.info(f"Collected {len(articles)} articles")
    return articles

async def upload_to_postgres(articles: List[Dict]) -> None:
    """
    Upload articles to PostgreSQL.
    
    Args:
        articles: List of article dictionaries to upload
    """
    if not articles:
        logger.warning("No articles to upload")
        return
    
    logger.info("Connecting to PostgreSQL...")
    db = DatabaseManager()
    
    try:
        await db.connect()
        logger.info(f"Uploading {len(articles)} articles to PostgreSQL...")
        await db.insert_articles(articles)
        logger.info("Upload complete")
    finally:
        await db.close()

async def main():
    """Main function to parse arguments and run the crawler."""
    parser = argparse.ArgumentParser(description="Run a crawler and upload data to PostgreSQL")
    parser.add_argument("crawler", help="Name of the crawler to run")
    parser.add_argument("--limit", type=int, help="Maximum number of articles to collect")
    
    args = parser.parse_args()
    
    # Run the crawler
    articles = run_crawler(args.crawler, args.limit)
    
    # Upload to PostgreSQL
    await upload_to_postgres(articles)

if __name__ == "__main__":
    asyncio.run(main()) 