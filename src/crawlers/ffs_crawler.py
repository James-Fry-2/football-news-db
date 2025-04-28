"""
Crawler for Fantasy Football Scout's articles section.
Extracts articles related to Premier League teams and players.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import logging
import re

from src.crawlers.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

class FFSCrawler(BaseCrawler):
    """
    Crawler for Fantasy Football Scout's articles section.
    Extracts articles related to Premier League teams and players.
    """
    
    BASE_URL = "https://www.fantasyfootballscout.co.uk/articles"
    
    def __init__(self):
        super().__init__()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def extract_date_from_url(self, url: str) -> Optional[datetime]:
        """
        Extract publication date from the article URL.
        
        Args:
            url: The article URL
            
        Returns:
            datetime object or None if date couldn't be extracted
        """
        # URL format: https://www.fantasyfootballscout.co.uk/2025/04/25/article-title
        date_pattern = r'fantasyfootballscout\.co\.uk/(\d{4})/(\d{2})/(\d{2})/'
        match = re.search(date_pattern, url)
        
        if match:
            try:
                year, month, day = map(int, match.groups())
                return datetime(year, month, day)
            except ValueError:
                logger.warning(f"Invalid date in URL: {url}")
                return None
        
        return None

    def extract_article_data(self, url: str) -> Optional[Dict]:
        """Extract article data from a Fantasy Football Scout article page."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_element = soup.find('h1')
            if not title_element:
                return None
            title = title_element.text.strip()
            
            # Extract content
            content_elements = soup.find_all('p')
            if not content_elements:
                return None
            content = ' '.join([p.text.strip() for p in content_elements])
            
            # Extract publication date from URL first
            published_date = self.extract_date_from_url(url)
            
            # If not found in URL, try to find it in the page
            if not published_date:
                date_element = soup.find('time')
                if date_element and date_element.get('datetime'):
                    try:
                        published_date = datetime.fromisoformat(date_element['datetime'].replace('Z', '+00:00'))
                    except ValueError:
                        # Try alternative date format
                        try:
                            date_str = date_element.text.strip()
                            published_date = datetime.strptime(date_str, '%B %d, %Y')
                        except ValueError:
                            pass
            
            # Extract teams and players mentioned in the article
            full_text = f"{title} {content}"
            entities = self.extract_mentioned_entities(full_text)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'published_date': published_date,
                'source': 'Fantasy Football Scout',
                'mentioned_teams': entities['teams'],
                'mentioned_players': entities['players']
            }
            
        except Exception as e:
            logger.error(f"Error extracting article data from {url}: {str(e)}")
            return None

    def crawl(self) -> List[Dict]:
        """Crawl Fantasy Football Scout's articles section."""
        articles = []
        try:
            response = self.session.get(self.BASE_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all article links - look for links with date pattern in href
            article_links = []
            
            # Method 1: Look for links with date pattern
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and re.search(r'/\d{4}/\d{2}/\d{2}/', href):
                    article_links.append(link)
            
            # Method 2: Look for links in article sections
            article_sections = soup.find_all('article') or soup.find_all('div', class_='article')
            for section in article_sections:
                for link in section.find_all('a', href=True):
                    href = link.get('href')
                    if href and href not in [l.get('href') for l in article_links]:
                        article_links.append(link)
            
            for link in article_links:
                href = link.get('href')
                if not href:
                    continue
                
                # Construct full URL
                full_url = href if href.startswith('http') else f"https://www.fantasyfootballscout.co.uk{href}"
                
                # Get the link text and surrounding content to check if it's Premier League related
                link_text = link.get_text().strip()
                parent_text = link.parent.get_text().strip()
                
                if self.is_premier_league_content(link_text) or self.is_premier_league_content(parent_text):
                    article_data = self.extract_article_data(full_url)
                    if article_data:
                        articles.append(article_data)
                        logger.info(f"Successfully crawled article: {article_data['title']}")
            
        except Exception as e:
            logger.error(f"Error crawling Fantasy Football Scout: {str(e)}")
        
        return articles 