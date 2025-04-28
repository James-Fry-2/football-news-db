"""
Template for creating new crawlers.
Copy this file and modify it to create a new crawler for a specific source.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import logging

from src.crawlers.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

class TemplateCrawler(BaseCrawler):
    """
    Template crawler for demonstration purposes.
    Replace 'Template' with the actual source name (e.g., ESPNCrawler).
    """
    
    # Base URL for the source
    BASE_URL = "https://example.com/football"
    
    def extract_article_data(self, url: str) -> Optional[Dict]:
        """
        Extract article data from the source's article page.
        
        Args:
            url: The URL of the article
            
        Returns:
            Dictionary containing article data or None if extraction failed
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title - modify selectors based on the source's HTML structure
            title_element = soup.find('h1')  # Replace with appropriate selector
            if not title_element:
                return None
            title = title_element.text.strip()
            
            # Extract content - modify selectors based on the source's HTML structure
            content_elements = soup.find_all('p')  # Replace with appropriate selector
            if not content_elements:
                return None
            content = ' '.join([p.text.strip() for p in content_elements])
            
            # Extract publication date - modify based on the source's date format
            date_element = soup.find('time')  # Replace with appropriate selector
            published_date = None
            if date_element and date_element.get('datetime'):
                try:
                    published_date = datetime.fromisoformat(date_element['datetime'].replace('Z', '+00:00'))
                except ValueError:
                    # Try alternative date parsing if the format is different
                    pass
            
            # Extract teams and players mentioned in the article
            full_text = f"{title} {content}"
            entities = self.extract_mentioned_entities(full_text)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'published_date': published_date,
                'source': 'Template Source',  # Replace with actual source name
                'mentioned_teams': entities['teams'],
                'mentioned_players': entities['players']
            }
            
        except Exception as e:
            logger.error(f"Error extracting article data from {url}: {str(e)}")
            return None

    def crawl(self) -> List[Dict]:
        """
        Crawl the source for Premier League articles.
        
        Returns:
            List of dictionaries containing article data
        """
        articles = []
        try:
            response = self.session.get(self.BASE_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all article links - modify selectors based on the source's HTML structure
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Check if it's an article link - modify condition based on the source's URL structure
                if 'article' in href:  # Replace with appropriate condition
                    # Construct full URL if needed
                    full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                    
                    # Get the link text and surrounding content to check if it's Premier League related
                    link_text = link.get_text().strip()
                    parent_text = link.parent.get_text().strip()
                    
                    if self.is_premier_league_content(link_text) or self.is_premier_league_content(parent_text):
                        article_data = self.extract_article_data(full_url)
                        if article_data:
                            articles.append(article_data)
                            logger.info(f"Successfully crawled article: {article_data['title']}")
            
        except Exception as e:
            logger.error(f"Error crawling source: {str(e)}")
        
        return articles 