"""
Enhanced Base Crawler with User-Agent Rotation

This module provides a sophisticated base crawler with automatic user-agent rotation
using the fake-useragent library for web scraping resilience.

Features:
- Automatic user-agent rotation from real-world browser statistics
- Configurable rotation intervals and browser types
- Support for desktop and mobile user agents
- Fallback mechanisms for robustness
- Integration with Premier League data filtering

Example Usage:

    # Basic usage with default user-agent rotation
    crawler = BaseCrawler(enable_user_agent_rotation=True)
    
    # Custom configuration for specific site requirements
    ua_config = {
        'browsers': ['Chrome', 'Firefox'],  # Only Chrome and Firefox
        'platforms': ['desktop'],           # Desktop only
        'os': ['Windows', 'Mac OS X'],      # Windows and Mac only
        'min_version': 110.0,               # Recent versions only
        'rotation_interval': 5              # Rotate every 5 requests
    }
    crawler = BaseCrawler(enable_user_agent_rotation=True, ua_config=ua_config)
    
    # Site-specific crawler with user-agent rotation
    bbc_crawler = SiteSpecificCrawler(
        'bbc', 
        enable_user_agent_rotation=True,
        ua_config={'rotation_interval': 3}
    )
    
    # Check user-agent status
    info = crawler.get_user_agent_info()
    print(f"Current UA: {info['current_ua']}")
    print(f"Rotation enabled: {info['rotation_enabled']}")

User-Agent Configuration Options:
- browsers: List of browser types to use
- platforms: List of platform types ('desktop', 'mobile', 'tablet')
- os: List of operating systems
- min_version: Minimum browser version
- rotation_interval: Number of requests before rotating (default: 10)
- fallback: Fallback user-agent string if generation fails
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging
import requests
import aiohttp
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import random
import time

try:
    from fake_useragent import UserAgent
    FAKE_USERAGENT_AVAILABLE = True
except ImportError:
    FAKE_USERAGENT_AVAILABLE = False
    UserAgent = None

from ..data.premier_league_data import PremierLeagueData

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """
    Base class for all football news crawlers.
    Provides common functionality including header management, session handling,
    user-agent rotation, and Premier League data integration.
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
    
    def __init__(self, db_session: AsyncSession = None, custom_headers: Dict[str, str] = None, 
                 enable_user_agent_rotation: bool = True, ua_config: Dict = None):
        """
        Initialize the crawler with database session and optional custom headers.
        
        Args:
            db_session: Database session for Premier League data
            custom_headers: Additional or override headers for this crawler
            enable_user_agent_rotation: Whether to enable automatic user-agent rotation
            ua_config: Configuration for fake-useragent (browsers, platforms, os, etc.)
        """
        # User-agent rotation setup
        self.enable_user_agent_rotation = enable_user_agent_rotation and FAKE_USERAGENT_AVAILABLE
        self.ua_config = ua_config or {}
        self.ua_generator = None
        self.last_ua_rotation = 0
        self.ua_rotation_interval = self.ua_config.get('rotation_interval', 10)  # Rotate every 10 requests
        self.request_count = 0
        
        # Initialize fake-useragent if available and enabled
        if self.enable_user_agent_rotation:
            self._initialize_user_agent_generator()
        
        # Build headers by merging defaults with custom headers
        self.headers = self.DEFAULT_HEADERS.copy()
        if custom_headers:
            self.headers.update(custom_headers)
        
        # Set initial user-agent if rotation is enabled
        if self.enable_user_agent_rotation and self.ua_generator:
            self.headers['User-Agent'] = self._get_fresh_user_agent()
        
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
    
    def _initialize_user_agent_generator(self):
        """Initialize the fake-useragent generator with custom configuration."""
        if not FAKE_USERAGENT_AVAILABLE:
            logger.warning("fake-useragent not available. User-agent rotation disabled.")
            return
        
        try:
            # Set default configuration optimized for news site scraping
            default_config = {
                'browsers': ['Chrome', 'Firefox', 'Edge', 'Safari'],  # Mainstream browsers
                'platforms': ['desktop', 'mobile'],  # Both desktop and mobile
                'os': ['Windows', 'Mac OS X', 'Linux', 'Android', 'iOS'],  # Major OS
                'min_version': 100.0,  # Recent browser versions
                'fallback': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            # Merge with user config
            config = {**default_config, **self.ua_config}
            
            # Create UserAgent instance with configuration
            self.ua_generator = UserAgent(
                browsers=config.get('browsers'),
                fallback=config.get('fallback')
            )
            
            logger.info(f"User-agent rotation initialized with config: {config}")
            
        except Exception as e:
            logger.error(f"Failed to initialize user-agent generator: {e}")
            self.ua_generator = None
            self.enable_user_agent_rotation = False
    
    def _get_fresh_user_agent(self) -> str:
        """Get a fresh user-agent string."""
        if not self.ua_generator:
            return self.DEFAULT_HEADERS['User-Agent']
        
        try:
            # Randomly choose between different browser types for variety
            browser_methods = [
                lambda: self.ua_generator.random,
                lambda: self.ua_generator.chrome,
                lambda: self.ua_generator.firefox,
                lambda: self.ua_generator.safari,
                lambda: self.ua_generator.edge,
            ]
            
            # Choose a random method and get user-agent
            chosen_method = random.choice(browser_methods)
            user_agent = chosen_method()
            
            logger.debug(f"Generated new user-agent: {user_agent}")
            return user_agent
            
        except Exception as e:
            logger.warning(f"Failed to generate user-agent: {e}. Using fallback.")
            return self.DEFAULT_HEADERS['User-Agent']
    
    def _maybe_rotate_user_agent(self):
        """Rotate user-agent if rotation is enabled and interval has passed."""
        if not self.enable_user_agent_rotation:
            return
        
        self.request_count += 1
        
        # Check if it's time to rotate
        if self.request_count % self.ua_rotation_interval == 0:
            new_ua = self._get_fresh_user_agent()
            self.update_headers({'User-Agent': new_ua})
            logger.debug(f"Rotated user-agent after {self.request_count} requests")
    
    def get_user_agent_info(self) -> Dict:
        """Get information about the current user-agent setup."""
        if not self.ua_generator:
            return {
                'rotation_enabled': False,
                'current_ua': self.headers.get('User-Agent', 'Unknown'),
                'fake_useragent_available': FAKE_USERAGENT_AVAILABLE
            }
        
        try:
            # Get detailed info about current UA
            ua_data = self.ua_generator.getRandom
            return {
                'rotation_enabled': self.enable_user_agent_rotation,
                'current_ua': self.headers.get('User-Agent', 'Unknown'),
                'request_count': self.request_count,
                'rotation_interval': self.ua_rotation_interval,
                'fake_useragent_available': FAKE_USERAGENT_AVAILABLE,
                'ua_details': ua_data,
                'config': self.ua_config
            }
        except Exception as e:
            logger.warning(f"Error getting UA info: {e}")
            return {
                'rotation_enabled': self.enable_user_agent_rotation,
                'current_ua': self.headers.get('User-Agent', 'Unknown'),
                'error': str(e)
            }

    async def get_aiohttp_session(self) -> aiohttp.ClientSession:
        """Get a properly configured aiohttp session with potentially rotated user-agent."""
        # Maybe rotate user-agent before creating session
        self._maybe_rotate_user_agent()
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
        Extract article data from a URL using sync requests with user-agent rotation.
        
        Args:
            url: The URL of the article
            
        Returns:
            Dictionary containing article data or None if extraction failed
        """
        try:
            # Maybe rotate user-agent before making request
            self._maybe_rotate_user_agent()
            
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
