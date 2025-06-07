from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging
import requests
import aiohttp
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..data.premier_league_data import PremierLeagueData

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """
    Base class for all football news crawlers.
    Provides common functionality including header management, session handling,
    and Premier League data integration.
    """
    #TODO: add a method to keep headers up to date
    # Default headers that work for most news sites
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    def __init__(self, db_session: AsyncSession = None, custom_headers: Dict[str, str] = None):
        """
        Initialize the crawler with database session and optional custom headers.
        
        Args:
            db_session: Database session for Premier League data
            custom_headers: Additional or override headers for this crawler
        """
        # Build headers by merging defaults with custom headers
        self.headers = self.DEFAULT_HEADERS.copy()
        if custom_headers:
            self.headers.update(custom_headers)
        
        # Set up requests session for synchronous requests
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Configure session settings
        self._configure_session()
        
        # Database session for Premier League data
        self.db_session = db_session
        self.pl_data = None
        self._data_initialized = False
    
    def _configure_session(self):
        """Configure the requests session with common settings."""
        # Set reasonable timeouts
        self.session.timeout = 30
        
        # Configure retries (you might want to add urllib3.util.Retry here)
        # For now, we'll handle retries in individual methods
        
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def get_headers_for_site(self, site_name: str) -> Dict[str, str]:
        """
        Get headers optimized for a specific site.
        Override this method in subclasses for site-specific header requirements.
        
        Args:
            site_name: Name of the site (e.g., 'bbc', 'sky_sports')
            
        Returns:
            Dictionary of headers for the site
        """
        # Base implementation returns default headers
        # Subclasses can override for site-specific needs
        return self.headers.copy()
    
    def update_headers(self, new_headers: Dict[str, str]):
        """
        Update headers for both sync and async sessions.
        
        Args:
            new_headers: Dictionary of headers to add/update
        """
        self.headers.update(new_headers)
        self.session.headers.update(new_headers)
    
    async def get_aiohttp_session(self) -> aiohttp.ClientSession:
        """Get a properly configured aiohttp session."""
        return aiohttp.ClientSession(headers=self.headers)
    
    async def initialize_data(self, db_session: AsyncSession = None):
        """Initialize Premier League data from database."""
        if self._data_initialized:
            return
        
        if db_session:
            self.db_session = db_session
            self.pl_data = PremierLeagueData(db_session)
            await self.pl_data.initialize()
            self._data_initialized = True
            logger.info("Successfully initialized Premier League data")
        else:
            logger.warning("No database session available for Premier League data")
    
    async def is_premier_league_content(self, text: str) -> bool:
        """
        Check if the content is related to Premier League teams or players.
        Uses cached data for performance.
        """
        if not self._data_initialized or not self.pl_data:
            logger.warning("Premier League data not initialized. Content check may be incomplete.")
            return True  # Allow content through if data not available
        
        return self.pl_data.is_premier_league_content(text)
    
    async def extract_mentioned_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract mentioned teams and players from text using database data.
        """
        if not self._data_initialized or not self.pl_data:
            logger.warning("Premier League data not initialized. Content check may be incomplete.")
            return {'teams': [], 'players': []}
        
        try:
            return self.pl_data.extract_mentioned_entities(text)
        except Exception as e:
            logger.error(f"Error extracting entities from database: {e}")
            return {'teams': [], 'players': []}
    
    @abstractmethod
    async def fetch_articles(self) -> List[Dict]:
        """
        Fetch articles from the source.
        
        Returns:
            List of dictionaries containing article data
        """
        pass
    
    def extract_article_data(self, url: str) -> Optional[Dict]:
        """
        Extract article data from a URL using sync requests.
        
        Args:
            url: The URL of the article
            
        Returns:
            Dictionary containing article data or None if extraction failed
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # This is a placeholder - subclasses should override this method
            # with their specific extraction logic
            logger.warning("Base extract_article_data method called - should be overridden by subclasses")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting article data from {url}: {str(e)}")
            return None
    
    async def extract_article_data_async(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """
        Extract article data from a URL using async requests.
        
        Args:
            session: aiohttp ClientSession
            url: The URL of the article
            
        Returns:
            Dictionary containing article data or None if extraction failed
        """
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                
                html = await response.text()
                
                # This is a placeholder - subclasses should override this method
                # with their specific extraction logic
                logger.warning("Base extract_article_data_async method called - should be overridden by subclasses")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting article data from {url}: {str(e)}")
            return None
    
    async def close(self):
        """Clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()

class SiteSpecificCrawler(BaseCrawler):
    """
    Example of how to create site-specific crawlers with custom headers.
    """
    
    # Site-specific header overrides
    SITE_HEADERS = {
        'bbc': {
            'Referer': 'https://www.bbc.co.uk/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        },
        'sky_sports': {
            'Referer': 'https://www.skysports.com/',
            'X-Requested-With': 'XMLHttpRequest'  # If needed for AJAX requests
        },
        'espn': {
            'Referer': 'https://www.espn.com/',
        }
    }
    
    def __init__(self, site_name: str, db_session: AsyncSession = None):
        """
        Initialize with site-specific headers.
        
        Args:
            site_name: Name of the site for header customization
            db_session: Database session
        """
        # Get custom headers for this site
        custom_headers = self.SITE_HEADERS.get(site_name, {})
        
        # Initialize base crawler with custom headers
        super().__init__(db_session, custom_headers)
        
        self.site_name = site_name
    
    def get_headers_for_site(self, site_name: str = None) -> Dict[str, str]:
        """Get headers optimized for the specific site."""
        target_site = site_name or self.site_name
        
        headers = self.headers.copy()
        
        # Add any additional site-specific headers
        if target_site in self.SITE_HEADERS:
            headers.update(self.SITE_HEADERS[target_site])
        
        return headers