"""
Crawler for Fantasy Football Scout's articles section.
Extracts articles related to Premier League teams and players.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp

from src.crawlers.base_crawler import BaseCrawler
from ..db.services.article_service import ArticleService

logger = logging.getLogger(__name__)

class FFSCrawler(BaseCrawler):
    """
    Crawler for Fantasy Football Scout's articles section.
    Extracts articles related to Premier League teams and players.
    """
    
    BASE_URL = "https://www.fantasyfootballscout.co.uk/articles"
    
    def __init__(self, article_service: ArticleService = None, db_session: AsyncSession = None):
        """
        Initialize FFS crawler with site-specific headers.
        
        Args:
            article_service: Service for saving articles to database
            db_session: Database session for Premier League data
        """
        # Initialize base crawler with FFS-specific headers
        super().__init__(db_session)
        
        self.article_service = article_service
        self.base_url = self.BASE_URL
        self.site_name = "Fantasy Football Scout"
    
    async def fetch_articles(self) -> List[Dict]:
        """
        Fetch articles from Fantasy Football Scout.
        
        Returns:
            List of article dictionaries
        """
        # Initialize Premier League data if we have a database session
        if self.db_session:
            await self.initialize_data(self.db_session)
        
        articles = []
        
        # Use the base crawler's method to get a properly configured session
        async with await self.get_aiohttp_session() as session:
            try:
                async with session.get(self.base_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch FFS: {response.status}")
                        return articles

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find all article links
                    article_links = soup.find_all('a', href=True)
                    
                    # Process each article
                    for link in article_links:
                        href = link.get('href')
                        if not href:
                            continue
                        
                        # Construct full URL
                        full_url = href if href.startswith('http') else f"https://www.fantasyfootballscout.co.uk{href}"
                        
                        # Get the link text and surrounding content to check if it's Premier League related
                        link_text = link.get_text().strip()
                        parent_text = link.parent.get_text().strip()
                        
                        if await self.is_premier_league_content(link_text) or await self.is_premier_league_content(parent_text):
                            article_data = await self.extract_article_data_async(session, full_url)
                            if article_data:
                                # Extract entities using database data
                                entities = await self.extract_mentioned_entities(
                                    f"{article_data['title']} {article_data['content']}"
                                )
                                article_data['teams'] = entities['teams']
                                article_data['players'] = entities['players']
                                
                                articles.append(article_data)
                                logger.info(f"Found Premier League article: {article_data['title']}")

            except Exception as e:
                logger.error(f"Error fetching FFS articles: {e}")

        return articles

    async def extract_article_data_async(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """
        Extract data from a Fantasy Football Scout article.
        
        Args:
            session: aiohttp ClientSession
            url: Article URL
            
        Returns:
            Dictionary containing article data or None if extraction failed
        """
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
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
                
                return {
                    'title': title,
                    'content': content,
                    'url': url,
                    'published_date': published_date,
                    'source': 'Fantasy Football Scout'
                }

        except Exception as e:
            logger.error(f"Error extracting article data from {url}: {str(e)}")
            return None

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