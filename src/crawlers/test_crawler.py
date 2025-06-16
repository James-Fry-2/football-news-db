import logging
import sys
import os
import argparse
import asyncio
from typing import Dict, Type

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import crawler registry
from src.crawlers.registry import CRAWLERS, get_crawler_class, get_available_crawlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def display_article(article):
    """Display article information in a formatted way."""
    print(f"\nTitle: {article['title']}")
    print(f"URL: {article['url']}")
    if article['published_date']:
        print(f"Published: {article['published_date']}")
    
    if article.get('mentioned_teams'):
        print(f"Teams mentioned: {', '.join(article['mentioned_teams'])}")
    
    if article.get('mentioned_players'):
        print(f"Players mentioned: {', '.join(article['mentioned_players'])}")
        
    print("-" * 80)

async def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Test football news crawlers')
    parser.add_argument('crawler', choices=get_available_crawlers(), 
                        help='The crawler to test')
    parser.add_argument('--limit', type=int, default=5,
                        help='Maximum number of articles to display (default: 5)')
    parser.add_argument('--verbose', action='store_true',
                        help='Display full article content')
    parser.add_argument('--headless', action='store_true',
                        help='Force headless mode (no visible browser)')
    parser.add_argument('--no-headless', action='store_true',
                        help='Force non-headless mode (visible browser)')
    parser.add_argument('--team', type=str,
                        help='Target specific team (BBC crawler only). Use --list-teams to see available teams')
    parser.add_argument('--list-teams', action='store_true',
                        help='List available teams for BBC crawler')
    parser.add_argument('--max-pages', type=int, default=2,
                        help='Maximum pages per team for BBC crawler (default: 2)')
    
    args = parser.parse_args()
    
    # Handle list teams request
    if args.list_teams:
        if args.crawler == 'bbc':
            from src.crawlers.bbc_crawler import BBCCrawler
            teams = BBCCrawler.get_available_teams()
            print("Available teams for BBC crawler:")
            for slug, name in teams.items():
                print(f"  {slug} - {name}")
        else:
            print(f"Team selection is only available for BBC crawler")
        return
    
    # Get the crawler class
    crawler_class = get_crawler_class(args.crawler)
    
    # Create an instance of the crawler
    # Handle special initialization for Goal crawler
    if args.crawler == 'goal':
        # Detect if running in Docker/container environment
        import os
        is_container = (
            os.path.exists('/.dockerenv') or 
            os.environ.get('DOCKER_CONTAINER') == 'true' or
            os.environ.get('DISPLAY') is None
        )
        
        # Determine headless mode based on arguments and environment
        if args.headless:
            headless_mode = True
        elif args.no_headless:
            headless_mode = False
        else:
            headless_mode = is_container  # Auto-detect based on environment
        
        print(f"Running Goal crawler in {'headless' if headless_mode else 'visible browser'} mode")
        
        # Goal crawler needs special parameters and works without database in test mode
        crawler = crawler_class(
            article_service=None,    # No database service in test mode
            db_session=None,         # No database session in test mode
            headless=headless_mode,  # Use determined headless mode
            max_pages=1              # Limit pages for testing
        )
    elif args.crawler == 'goal_requests':
        # Goal requests crawler needs special parameters
        crawler = crawler_class(
            article_service=None,    # No database service in test mode
            db_session=None,         # No database session in test mode
            max_pages=1              # Limit pages for testing
        )
        print("Running Goal requests crawler (no browser needed)")
    elif args.crawler == 'bbc':
        # BBC crawler with team-specific options
        if args.team:
            print(f"Running BBC crawler for team: {args.team}")
        else:
            print("Running BBC crawler for all teams")
        
        crawler = crawler_class(
            target_team=args.team,
            max_pages_per_team=args.max_pages
        )
    else:
        # Other crawlers can be initialized normally
        crawler = crawler_class()
    
    # Run the crawler
    print(f"Testing {args.crawler.upper()} crawler...")
    articles = await crawler.crawl()  # Add await here
    
    # Display results
    print(f"\nFound {len(articles)} articles:")
    
    # Limit the number of articles to display
    display_articles = articles[:args.limit]
    
    for article in display_articles:
        display_article(article)
        
        # Display full content if verbose mode is enabled
        if args.verbose and 'content' in article:
            print("\nContent:")
            print(article['content'][:500] + "..." if len(article['content']) > 500 else article['content'])
            print("-" * 80)
    
    # Show summary if there are more articles than the limit
    if len(articles) > args.limit:
        print(f"\n... and {len(articles) - args.limit} more articles (use --limit to see more)")

if __name__ == "__main__":
    asyncio.run(main()) 