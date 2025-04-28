import logging
import sys
import os
import argparse
from typing import Dict, Type

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import all crawlers
from src.crawlers.bbc_crawler import BBCCrawler
# Import additional crawlers here as they are created
# from src.crawlers.espn_crawler import ESPNCrawler
# from src.crawlers.skysports_crawler import SkySportsCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Dictionary mapping crawler names to their classes
CRAWLERS: Dict[str, Type] = {
    'bbc': BBCCrawler,
    # Add additional crawlers here as they are created
    # 'espn': ESPNCrawler,
    # 'skysports': SkySportsCrawler,
}

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

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Test football news crawlers')
    parser.add_argument('crawler', choices=CRAWLERS.keys(), 
                        help='The crawler to test')
    parser.add_argument('--limit', type=int, default=5,
                        help='Maximum number of articles to display (default: 5)')
    parser.add_argument('--verbose', action='store_true',
                        help='Display full article content')
    
    args = parser.parse_args()
    
    # Get the crawler class
    crawler_class = CRAWLERS[args.crawler]
    
    # Create an instance of the crawler
    crawler = crawler_class()
    
    # Run the crawler
    print(f"Testing {args.crawler.upper()} crawler...")
    articles = crawler.crawl()
    
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
    main() 