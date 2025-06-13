"""
Crawler for Fantasy Football Scout's articles section.
Extracts articles related to Premier League teams and players.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
from datetime import datetime
import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp
from urllib.parse import urljoin

from src.crawlers.base_crawler import BaseCrawler
from ..db.services.article_service import ArticleService

logger = logging.getLogger(__name__)

class FFSCrawler(BaseCrawler):
    """
    Crawler for Fantasy Football Scout's articles section.
    Extracts articles related to Premier League teams and players.
    """
    
    BASE_URL = "https://www.fantasyfootballscout.co.uk"
    SECTIONS = {
        'scout_reports': {
            'url': '/category/scout-reports',
            'article_class': 'latest-home-posts homepost',
            'pattern': None  # No specific pattern needed for scout reports
        },
        'captains': {
            'url': '/category/team-selection/fpl-captains',
            'article_class': None,
            'pattern': r'captain.*gameweek'  # Articles must contain both "captain" and "gameweek"
        },
        'scout_notes': {
            'url': '/category/scout-notes',
            'article_class': None,
            'pattern': None  # No specific pattern needed for scout notes
        }
    }
    
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
        self.processed_urls: Set[str] = set()
    
    async def fetch_section_articles(self, session: aiohttp.ClientSession, section: str, section_config: dict, page: int = 1) -> List[Dict]:
        """
        Fetch articles from a specific section with pagination support.
        
        Args:
            session: aiohttp session
            section: Section name
            section_config: Section configuration
            page: Page number to fetch
            
        Returns:
            List of article dictionaries
        """
        articles = []
        
        # Construct the URL with pagination if needed
        url = urljoin(self.base_url, section_config['url'])
        if page > 1:
            url = f"{url}/page/{page}"
            
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch {url}: {response.status}")
                    return articles

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find articles based on section configuration
                if section_config['article_class']:
                    article_containers = soup.find_all('div', class_=section_config['article_class'])
                    for container in article_containers:
                        links = container.find_all('a', href=True)
                        for link in links:
                            await self.process_article_link(session, link, section_config, articles)
                else:
                    # If no specific class, look for all article links
                    links = soup.find_all('a', href=True)
                    for link in links:
                        await self.process_article_link(session, link, section_config, articles)
                        
        except Exception as e:
            logger.error(f"Error fetching section {section} page {page}: {e}")
            
        return articles

    def normalize_url(self, href: str) -> str:
        """
        Normalize URL for consistent duplicate detection.
        
        Args:
            href: The URL to normalize
            
        Returns:
            Normalized URL string
        """
        # Remove fragment identifiers (like #comments)
        href = href.split('#')[0]
        
        # Ensure URL is absolute
        if not href.startswith('http'):
            href = urljoin(self.base_url, href)
            
        # Remove trailing slashes and convert to lowercase
        href = href.rstrip('/').lower()
        
        return href

    async def process_article_link(self, session: aiohttp.ClientSession, link: BeautifulSoup, section_config: dict, articles: List[Dict]):
        """Process a single article link and add it to the articles list if valid."""
        href = link.get('href', '')
        
        # Skip if it's a comments URL
        if '#comments' in href:
            return
            
        # Ensure URL is absolute for pattern matching
        original_href = href
        if not href.startswith('http'):
            original_href = urljoin(self.base_url, href)
            
        # Check if URL matches FFS article pattern
        if not re.search(r'/\d{4}/\d{2}/\d{2}/', original_href):
            return
            
        # Check section-specific pattern if it exists
        if section_config['pattern']:
            link_text = link.get_text().lower()
            if not re.search(section_config['pattern'], link_text):
                return
                
        # Normalize URL for duplicate checking
        normalized_href = self.normalize_url(href)
        
        # Skip if already processed
        if normalized_href in self.processed_urls:
            return
                
        # Extract and validate article data (use original absolute URL)
        article_data = await self.extract_article_data(session, original_href)
        if article_data:
            self.processed_urls.add(normalized_href)
            articles.append(article_data)
            logger.info(f"Found article: {article_data['title']}")

    async def fetch_articles(self) -> List[Dict]:
        """
        Required implementation of BaseCrawler's abstract method.
        Delegates to crawl() for the actual implementation.
        
        Returns:
            List of article dictionaries
        """
        return await self.crawl()

    async def crawl(self) -> List[Dict]:
        """
        Crawl Fantasy Football Scout's articles section.
        
        Returns:
            List of article dictionaries
        """
        # Initialize Premier League data if we have a database session
        if self.db_session:
            await self.initialize_data(self.db_session)
        
        all_articles = []
        self.processed_urls.clear()
        
        # Use the base crawler's method to get a properly configured session
        async with await self.get_aiohttp_session() as session:
            # Process each section
            for section, config in self.SECTIONS.items():
                page = 1
                while True:
                    articles = await self.fetch_section_articles(session, section, config, page)
                    if not articles:  # No more articles found
                        break
                    all_articles.extend(articles)
                    page += 1
                    
                    # Limit to 5 pages per section to avoid overloading
                    if page > 5:
                        break

        return all_articles

    def extract_text_content(self, soup: BeautifulSoup) -> str:
        """
        Extract text content from p, h2, and ul tags in the article while maintaining original order.
        
        Args:
            soup: BeautifulSoup object of the article
            
        Returns:
            String containing all extracted text content in original order
        """
        content_parts = []
        
        # Find the article content section
        article_content = soup.find('section', class_='entry-content')
        if not article_content:
            return ""
            
        # Process all elements in order
        for element in article_content.find_all(['p', 'h2', 'ul']):
            if element.name == 'ul':
                # For ul tags, get all li elements
                list_items = [li.text.strip() for li in element.find_all('li')]
                if list_items:
                    content_parts.extend(list_items)
            else:
                # For p and h2 tags, get their text directly
                text = element.text.strip()
                if text:
                    content_parts.append(text)
        
        # Join all content parts with newlines
        return '\n'.join(filter(None, content_parts))

    async def extract_article_data(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """Extract article data from a Fantasy Football Scout article page asynchronously."""
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

                # Extract content using the new method
                content = self.extract_text_content(soup)

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
                entities = await self.extract_mentioned_entities(full_text)

                return {
                    'title': title,
                    'content': content,
                    'url': url,
                    'published_date': published_date,
                    'source': 'Fantasy Football Scout',
                    'teams': entities['teams'],
                    'players': entities['players']
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

    async def extract_mentioned_entities(self, text: str) -> Dict:
        """Extract teams and players mentioned in the text."""
        teams = []
        players = []
        
        # Implement your logic to extract teams and players from the text
        # This is a placeholder and should be replaced with actual implementation
        # For example, you can use regular expressions or a named entity recognition library
        
        return {
            'teams': teams,
            'players': players
        }
