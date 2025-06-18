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

from src.crawlers.registry import CRAWLERS, get_crawler_class, get_available_crawlers, is_valid_crawler
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

async def run_crawler(crawler_name: str, limit: int = None, target_team: str = None, max_pages: int = 3) -> List[Dict]:
    """
    Run a crawler and return the collected articles.
    
    Args:
        crawler_name: Name of the crawler to run
        limit: Maximum number of articles to collect (None for no limit)
        target_team: Specific team to crawl (BBC only)
        max_pages: Maximum pages per team (BBC only)
        
    Returns:
        List of article dictionaries
    """
    if not is_valid_crawler(crawler_name):
        logger.error(f"Unknown crawler: {crawler_name}")
        logger.info(f"Available crawlers: {', '.join(get_available_crawlers())}")
        return []
    
    # Connect to database
    await Database.connect_db(DATABASE_URL)
    
    try:
        # Create database session
        async with Database.get_session() as session:
            # Create article service
            article_service = ArticleService(session)
            
            # Create crawler instance with database services
            crawler_class = get_crawler_class(crawler_name)
            
            if crawler_name == "goal":
                crawler = crawler_class(article_service, session, headless=True)
            elif crawler_name == "bbc":
                # BBC crawler with team-specific options
                if target_team:
                    logger.info(f"Targeting specific team: {target_team}")
                crawler = crawler_class(
                    article_service,
                    session,
                    target_team=target_team,
                    max_pages_per_team=max_pages
                )
            else:
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
    parser.add_argument("crawler", nargs='?', help="Name of the crawler to run")
    parser.add_argument("--limit", type=int, help="Maximum number of articles to collect")
    parser.add_argument("--team", type=str, help="Target specific team (BBC crawler only). Use --list-teams to see available teams")
    parser.add_argument("--list-teams", action="store_true", help="List available teams for BBC crawler")
    parser.add_argument("--max-pages", type=int, default=3, help="Maximum pages per team for BBC crawler (default: 3)")
    
    args = parser.parse_args()
    
    # Handle list teams request
    if args.list_teams:
        # Default to BBC if no crawler specified with --list-teams
        crawler_name = args.crawler or 'bbc'
        if crawler_name == 'bbc':
            from src.crawlers.bbc_crawler import BBCCrawler
            teams = BBCCrawler.get_available_teams()
            print("Available teams for BBC crawler:")
            for slug, name in teams.items():
                print(f"  {slug} - {name}")
            print(f"\nUsage: python run_crawler.py bbc --team {list(teams.keys())[0]}")
        else:
            print(f"Team selection is only available for BBC crawler")
        return
    
    # Validate that crawler is provided for non-list operations
    if not args.crawler:
        parser.error("crawler argument is required unless using --list-teams")
    
    # Run the crawler (it will automatically save to database)
    articles = await run_crawler(args.crawler, args.limit, args.team, args.max_pages)
    
    logger.info(f"Process completed. {len(articles)} articles processed.")

if __name__ == "__main__":
    asyncio.run(main()) 