from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import aiohttp

from .base_crawler import BaseCrawler
from ..db.services.article_service import ArticleService

logger = logging.getLogger(__name__)

class BBCCrawler(BaseCrawler):
    """Crawler for BBC Sport football articles."""
    
    # BBC-specific header requirements
    BBC_HEADERS = {
        'Referer': 'https://www.bbc.co.uk/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    def __init__(self, article_service: ArticleService = None, db_session: AsyncSession = None,
                 enable_user_agent_rotation: bool = True):
        """
        Initialize BBC crawler with site-specific headers and user-agent rotation.
        
        Args:
            article_service: Service for saving articles to database
            db_session: Database session for Premier League data
            enable_user_agent_rotation: Whether to enable user-agent rotation
        """
        # Configure user-agent rotation for BBC (conservative approach)
        ua_config = {
            'browsers': ['Chrome', 'Firefox', 'Edge'],  # Mainstream browsers for news sites
            'platforms': ['desktop'],  # BBC works better with desktop UAs
            'os': ['Windows', 'Mac OS X', 'Linux'],  # Major desktop OS
            'min_version': 110.0,  # Recent but not bleeding edge
            'rotation_interval': 8  # Conservative rotation for BBC
        }
        
        # Initialize base crawler with BBC-specific headers and UA rotation
        super().__init__(db_session, self.BBC_HEADERS, enable_user_agent_rotation, ua_config)
        
        self.article_service = article_service
        self.base_url = "https://www.bbc.co.uk/sport/football"
        self.site_name = "BBC Sport"
    
    async def fetch_articles(self) -> List[Dict]:
        """
        Fetch articles from BBC Sport football section.
        
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
                        logger.error(f"Failed to fetch BBC Sport: {response.status}")
                        return articles

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find all article links
                    article_links = self._extract_article_links(soup)
                    
                    # Process each article
                    for article_url in article_links:
                        article_data = await self.extract_article_data_async(session, article_url)
                        if article_data:
                            # Check if Premier League content
                            if await self.is_premier_league_content(article_data['content']):
                                # Extract entities using database data
                                entities = await self.extract_mentioned_entities(
                                    f"{article_data['title']} {article_data['content']}"
                                )
                                article_data['teams'] = entities['teams']
                                article_data['players'] = entities['players']
                                
                                articles.append(article_data)
                                logger.info(f"Found Premier League article: {article_data['title']}")

            except Exception as e:
                logger.error(f"Error fetching BBC Sport articles: {e}")

        return articles
    
    def _extract_article_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract article URLs from BBC Sport homepage.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of article URLs
        """
        article_links = []
        
        # BBC Sport uses various selectors for article links
        selectors = [
            'a[href*="/sport/football/"]',  # General football links
            '.media__link',  # Media links
            '.gs-c-promo-heading a',  # Promo headings
            '[data-testid="internal-link"]'  # Test ID links
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if self._is_valid_article_link(href):
                    full_url = self._build_full_url(href)
                    if full_url not in article_links:
                        article_links.append(full_url)
        
        logger.info(f"Found {len(article_links)} potential article links")
        return article_links
    
    def _is_valid_article_link(self, href: str) -> bool:
        """
        Check if a link is a valid BBC Sport football article.
        
        Args:
            href: The href attribute from the link
            
        Returns:
            True if the link appears to be a football article
        """
        if not href:
            return False
        
        # Must contain football in the path
        if '/sport/football/' not in href:
            return False
        
        # Exclude certain types of pages
        exclusions = [
            '/football#',  # Hash links
            '/football?',  # Query parameters without articles
            '/football/tables',  # League tables
            '/football/fixtures',  # Fixture lists
            '/football/results',  # Results pages
            '/football/live',  # Live pages
            '/football/teams',  # Team directory
            '/football/gossip',  # Gossip column (might want to include this)
        ]
        
        for exclusion in exclusions:
            if exclusion in href:
                return False
        
        return True
    
    def _build_full_url(self, href: str) -> str:
        """
        Build full URL from href.
        
        Args:
            href: Relative or absolute URL
            
        Returns:
            Full URL
        """
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return f"https://www.bbc.co.uk{href}"
        else:
            return f"https://www.bbc.co.uk/sport/football/{href}"
    
    async def extract_article_data_async(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """
        Extract data from a BBC Sport article.
        
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
                
                # Extract article components
                title = self._extract_title(soup)
                content = self._extract_content(soup)
                published_date = self._extract_published_date(soup)
                author = self._extract_author(soup)
                
                if not all([title, content]):
                    logger.warning(f"Missing essential data for {url}")
                    return None
                
                return {
                    'url': url,
                    'title': title,
                    'content': content,
                    'published_date': published_date,
                    'source': self.site_name,
                    'author': author
                }

        except Exception as e:
            logger.error(f"Error extracting article data from {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title."""
        # BBC uses various title selectors
        selectors = [
            'h1[data-testid="headline"]',  # New BBC layout
            'h1.story-headline',  # Classic layout
            'h1',  # Fallback
            '.story-headline h1',  # Alternative
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract article content."""
        content_parts = []
        
        # BBC article content selectors
        selectors = [
            '[data-component="text-block"] p',  # New layout
            '.story-body p',  # Classic layout
            'article p',  # Generic article paragraphs
            '.post-content p',  # Alternative layout
        ]
        
        for selector in selectors:
            paragraphs = soup.select(selector)
            if paragraphs:
                content_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                break
        
        # Fallback: get all paragraphs
        if not content_parts:
            paragraphs = soup.find_all('p')
            content_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
        
        return ' '.join(content_parts)
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract publication date."""
        # Try different date selectors
        selectors = [
            'time[datetime]',
            '[data-testid="timestamp"] time',
            '.date time',
            '.story-date time'
        ]
        
        for selector in selectors:
            time_element = soup.select_one(selector)
            if time_element and time_element.get('datetime'):
                try:
                    date_str = time_element['datetime']
                    # Handle different BBC date formats
                    if 'T' in date_str:
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        return datetime.fromisoformat(date_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author."""
        selectors = [
            '[data-testid="byline"] span',
            '.byline',
            '.author',
            '[rel="author"]'
        ]
        
        for selector in selectors:
            author_element = soup.select_one(selector)
            if author_element:
                return author_element.get_text().strip()
        
        return None
    
    # For backward compatibility with test scripts
    async def crawl(self) -> List[Dict]:
        """Crawl method for compatibility with test scripts."""
        return await self.fetch_articles()