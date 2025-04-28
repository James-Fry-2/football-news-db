import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.crawlers.bbc_crawler import BBCCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    crawler = BBCCrawler()
    articles = crawler.crawl()
    
    print(f"\nFound {len(articles)} Premier League articles:")
    for article in articles:
        print(f"\nTitle: {article['title']}")
        print(f"URL: {article['url']}")
        if article['published_date']:
            print(f"Published: {article['published_date']}")
        
        if article['mentioned_teams']:
            print(f"Teams mentioned: {', '.join(article['mentioned_teams'])}")
        
        if article['mentioned_players']:
            print(f"Players mentioned: {', '.join(article['mentioned_players'])}")
            
        print("-" * 80)

if __name__ == "__main__":
    main() 