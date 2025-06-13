#!/usr/bin/env python3
"""
Docker-compatible script to test crawlers in the webscraper container.
This script properly handles async operations and database sessions.
"""

import asyncio
import argparse
import sys
import os
from typing import Dict, Type, List
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crawlers.registry import CRAWLERS, get_crawler_class, get_available_crawlers, is_valid_crawler
from src.db.database import get_async_session
from src.db.services.article_service import ArticleService
from loguru import logger

def display_article(article: Dict, verbose: bool = False):
    """Display article information in a formatted way."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Title: {article['title']}")
    logger.info(f"URL: {article['url']}")
    logger.info(f"Source: {article['source']}")
    
    if article.get('published_date'):
        logger.info(f"Published: {article['published_date']}")
    
    if article.get('author'):
        logger.info(f"Author: {article['author']}")
    
    if article.get('teams'):
        logger.info(f"Teams mentioned: {', '.join(article['teams'])}")
    
    if article.get('players'):
        logger.info(f"Players mentioned: {', '.join(article['players'])}")
    
    if verbose and article.get('content'):
        content_preview = article['content'][:500] + "..." if len(article['content']) > 500 else article['content']
        logger.info(f"\nContent preview:\n{content_preview}")
    
    logger.info(f"{'='*60}")

async def test_crawler_with_db(crawler_name: str, limit: int = 5, verbose: bool = False, save_to_db: bool = False):
    """Test a crawler with proper database integration."""
    if not is_valid_crawler(crawler_name):
        logger.error(f"Unknown crawler: {crawler_name}")
        logger.info(f"Available crawlers: {', '.join(get_available_crawlers())}")
        return

    logger.info(f"Testing {crawler_name.upper()} crawler...")
    
    crawler_class = get_crawler_class(crawler_name)
    articles = []
    
    try:
        # Create database session if needed
        if save_to_db:
            async with get_async_session() as session:
                article_service = ArticleService(session)
                crawler = crawler_class(article_service=article_service, db_session=session)
                
                logger.info("Running crawler with database integration...")
                articles = await crawler.fetch_articles()
                
                # Save articles to database
                if articles:
                    logger.info(f"Saving {len(articles)} articles to database...")
                    saved_count = 0
                    for article in articles:
                        try:
                            await article_service.save_article(
                                title=article['title'],
                                url=article['url'],
                                content=article['content'],
                                source=article['source'],
                                published_date=article.get('published_date'),
                                author=article.get('author')
                            )
                            saved_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to save article: {e}")
                    
                    logger.info(f"Successfully saved {saved_count} articles to database")
                
                await crawler.close()
        else:
            # Test without database
            crawler = crawler_class()
            logger.info("Running crawler without database integration...")
            articles = await crawler.fetch_articles()
            await crawler.close()
        
        # Display results
        logger.info(f"\n🎉 Found {len(articles)} articles from {crawler_name.upper()}")
        
        if not articles:
            logger.warning("No articles found. This might indicate:")
            logger.warning("- Site structure has changed")
            logger.warning("- Network connectivity issues")
            logger.warning("- Rate limiting or blocking")
            return
        
        # Display limited number of articles
        display_articles = articles[:limit]
        
        for i, article in enumerate(display_articles, 1):
            logger.info(f"\n📰 Article {i}:")
            display_article(article, verbose)
        
        # Show summary if there are more articles than the limit
        if len(articles) > limit:
            logger.info(f"\n... and {len(articles) - limit} more articles (use --limit to see more)")
        
        # Show crawler-specific info
        if hasattr(crawler, 'get_user_agent_info'):
            ua_info = crawler.get_user_agent_info()
            logger.info(f"\n🔧 User-Agent Info:")
            logger.info(f"Rotation enabled: {ua_info.get('rotation_enabled', 'Unknown')}")
            logger.info(f"Request count: {ua_info.get('request_count', 'Unknown')}")
            logger.info(f"Current UA: {ua_info.get('current_ua', 'Unknown')[:80]}...")

    except Exception as e:
        logger.error(f"Error testing {crawler_name} crawler: {e}")
        raise

async def test_all_crawlers(limit: int = 3, verbose: bool = False):
    """Test all available crawlers."""
    logger.info("🚀 Testing all crawlers...")
    
    results = {}
    
    for crawler_name in get_available_crawlers():
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing {crawler_name.upper()} crawler")
        logger.info(f"{'='*80}")
        
        try:
            start_time = datetime.now()
            await test_crawler_with_db(crawler_name, limit=limit, verbose=verbose)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            results[crawler_name] = {'status': 'success', 'duration': duration}
            logger.info(f"✅ {crawler_name.upper()} completed in {duration:.2f} seconds")
        except Exception as e:
            results[crawler_name] = {'status': 'failed', 'error': str(e)}
            logger.error(f"❌ {crawler_name.upper()} failed: {e}")
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("📊 CRAWLER TEST SUMMARY")
    logger.info(f"{'='*80}")
    
    for crawler_name, result in results.items():
        if result['status'] == 'success':
            logger.info(f"✅ {crawler_name.upper()}: Success ({result['duration']:.2f}s)")
        else:
            logger.error(f"❌ {crawler_name.upper()}: Failed - {result['error']}")

async def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description='Test football news crawlers in Docker')
    parser.add_argument('crawler', nargs='?', choices=get_available_crawlers() + ['all'], 
                        help='The crawler to test (or "all" for all crawlers)')
    parser.add_argument('--limit', type=int, default=5,
                        help='Maximum number of articles to display (default: 5)')
    parser.add_argument('--verbose', action='store_true',
                        help='Display full article content preview')
    parser.add_argument('--save-to-db', action='store_true',
                        help='Save articles to database (requires DB connection)')
    parser.add_argument('--list', action='store_true',
                        help='List available crawlers')
    
    args = parser.parse_args()
    
    if args.list:
        logger.info("Available crawlers:")
        for name in get_available_crawlers():
            logger.info(f"  - {name}")
        return
    
    if not args.crawler:
        logger.error("Please specify a crawler to test (or 'all')")
        parser.print_help()
        return
    
    # Configure logging for better Docker output
    logger.remove()
    logger.add(sys.stdout, 
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
               level="INFO")
    
    logger.info("🐳 Running crawler tests in Docker environment")
    logger.info(f"Testing with limit: {args.limit}, verbose: {args.verbose}, save-to-db: {args.save_to_db}")
    
    if args.crawler == 'all':
        await test_all_crawlers(limit=args.limit, verbose=args.verbose)
    else:
        await test_crawler_with_db(
            args.crawler, 
            limit=args.limit, 
            verbose=args.verbose, 
            save_to_db=args.save_to_db
        )
    
    logger.info("🎯 Crawler testing completed!")

if __name__ == "__main__":
    asyncio.run(main()) 