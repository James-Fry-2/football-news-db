"""
Goal.com Crawler with Playwright for JavaScript Rendering

Enhanced Goal.com crawler that uses Playwright to handle JavaScript-heavy content
and extract article links that are dynamically loaded.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import asyncio
import re

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None
    Browser = None
    Page = None

from .base_crawler import BaseCrawler
from ..db.services.article_service import ArticleService

logger = logging.getLogger(__name__)

class GoalNewsPlaywrightCrawler(BaseCrawler):
    """Goal News Crawler using Playwright for JavaScript-rendered content."""
    
    def __init__(self, article_service: ArticleService = None, db_session: AsyncSession = None,
                 enable_user_agent_rotation: bool = True, max_pages: int = 3, headless: bool = True):
        """
        Initialize Goal.com crawler with Playwright support.
        
        Args:
            article_service: Service for saving articles to database
            db_session: Database session for Premier League data
            enable_user_agent_rotation: Whether to enable user-agent rotation
            max_pages: Maximum number of pages to crawl (default: 3, reduced for Playwright)
            headless: Whether to run browser in headless mode
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required for Goal.com crawler. Install with: pip install playwright")
        
        # Initialize base crawler (we'll override session handling for Playwright)
        super().__init__(db_session, None, enable_user_agent_rotation, None)
        
        self.article_service = article_service
        self.base_url = "https://www.goal.com/en-gb/premier-league"
        self.news_base_url = "https://www.goal.com/en-gb/premier-league/news"
        self.site_name = "Goal News"
        self.max_pages = max_pages
        self.headless = headless
        
        # Track processed URLs to avoid duplicates
        self.processed_urls = set()
        
        # Playwright-specific settings
        self.browser = None
        self.context = None
    
    async def _setup_playwright(self):
        """Setup Playwright browser and context."""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with optimized settings for scraping
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # Speed up loading
                    '--disable-javascript-harmony-shipping',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-field-trial-config',
                    '--disable-back-forward-cache',
                    '--disable-ipc-flooding-protection'
                ]
            )
            
            # Create context with realistic browser settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self.headers.get('User-Agent'),
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            logger.info("Playwright browser setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup Playwright: {e}")
            raise
    
    async def _cleanup_playwright(self):
        """Clean up Playwright resources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("Playwright resources cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up Playwright: {e}")
    
    async def fetch_articles(self) -> List[Dict]:
        """
        Fetch articles from Goal.com Premier League section using Playwright.
        
        Returns:
            List of article dictionaries
        """
        # Initialize Premier League data if we have a database session
        if self.db_session:
            await self.initialize_data(self.db_session)
        
        articles = []
        
        try:
            # Setup Playwright
            await self._setup_playwright()
            
            # Create a new page
            page = await self.context.new_page()
            
            # Set up page event listeners for debugging
            if not self.headless:
                page.on("console", lambda msg: logger.debug(f"Console: {msg.text}"))
                page.on("pageerror", lambda error: logger.error(f"Page error: {error}"))
            
            # Skip main Premier League page and go directly to paginated news section
            # (Main page commented out to focus on specific news pagination)
            # logger.info(f"Fetching main Premier League page: {self.base_url}")
            # main_page_articles = await self._fetch_page_articles_playwright(page, self.base_url)
            # articles.extend(main_page_articles)
            
            # Fetch articles from paginated news section
            for page_num in range(1, self.max_pages + 1):
                # Try different URL patterns for Goal.com news
                url_patterns = [
                    f"{self.news_base_url}/{page_num}/2kwbbcootiqqgmrzs6o5inle5",  # Original pattern
                    f"{self.news_base_url}?page={page_num}",                      # Query parameter pattern
                    f"{self.news_base_url}/page/{page_num}",                      # Page path pattern
                    f"{self.news_base_url}",                                      # Just the base news URL
                ]
                
                for i, page_url in enumerate(url_patterns):
                    logger.info(f"Trying Goal.com news URL pattern {i+1}: {page_url}")
                    
                    page_articles = await self._fetch_page_articles_playwright(page, page_url)
                    if page_articles:
                        articles.extend(page_articles)
                        logger.info(f"Found {len(page_articles)} articles with URL pattern {i+1}")
                        break  # Success with this pattern, break inner loop
                    else:
                        logger.info(f"No articles found with URL pattern {i+1}")
                        if i < len(url_patterns) - 1:
                            await asyncio.sleep(1)  # Brief pause between pattern attempts
                
                # If we found articles with any pattern, continue to next page
                if page_articles:
                    logger.info(f"Found {len(page_articles)} new articles on page {page_num}")
                    # Add delay between pages
                    await asyncio.sleep(2)
                else:
                    logger.info(f"No articles found on page {page_num} with any URL pattern")
                    # Try next page anyway, might just be a gap
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Error fetching Goal.com articles with Playwright: {e}")
        finally:
            await self._cleanup_playwright()
        
        # Remove duplicates based on URL
        unique_articles = []
        seen_urls = set()
        for article in articles:
            url = article['url']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        logger.info(f"Total unique articles found: {len(unique_articles)}")
        return unique_articles
    
    async def _fetch_page_articles_playwright(self, page: Page, page_url: str) -> List[Dict]:
        """
        Fetch articles from a specific Goal.com page using Playwright.
        
        Args:
            page: Playwright Page instance
            page_url: URL of the page to fetch
            
        Returns:
            List of article dictionaries from this page
        """
        articles = []
        
        try:
            # Navigate to the page with increased timeout
            logger.info(f"Attempting to navigate to: {page_url}")
            response = await page.goto(page_url, wait_until='networkidle', timeout=90000)  # Increased to 90 seconds
            
            # Log response details
            if response:
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response URL: {response.url}")
                if response.status >= 400:
                    logger.error(f"HTTP error {response.status} for {page_url}")
            
            logger.info(f"Successfully navigated to: {page_url}")
            
            # Log the current URL to check for redirects
            current_url = page.url
            if current_url != page_url:
                logger.info(f"Page redirected to: {current_url}")
            
            # Wait for potential dynamic content to load
            try:
                # Wait for article cards to appear (increased timeout)
                await page.wait_for_selector('article.card, .news-card, [data-testid="card"]', timeout=20000)  # Increased to 20 seconds
                logger.info("Article cards loaded successfully")
            except Exception as e:
                logger.warning(f"Article cards selector not found: {e}")
                # Try alternative selectors
                try:
                    await page.wait_for_selector('a[href*="/lists/"], a[href*="/news/"]', timeout=15000)  # Increased to 15 seconds
                    logger.info("Found alternative article links")
                except Exception as e2:
                    logger.warning(f"No article links found: {e2}")
                # Wait longer for any dynamic content
                await asyncio.sleep(8)  # Increased from 5 to 8 seconds
            
            # Check if we can find any content at all
            page_content = await page.content()
            if len(page_content) < 1000:
                logger.warning(f"Page content seems very small: {len(page_content)} characters")
            else:
                logger.info(f"Page content loaded: {len(page_content)} characters")
            
            # Scroll down to trigger any lazy loading with increased waits
            logger.debug("Scrolling to trigger lazy loading...")
            await page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight / 2);
            """)
            await asyncio.sleep(3)  # Increased from 2 to 3 seconds
            
            await page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
            """)
            await asyncio.sleep(5)  # Increased from 3 to 5 seconds
            
            # Get the page content after JavaScript execution
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract article links using enhanced selectors
            article_links = self._extract_article_links_enhanced(soup)
            logger.info(f"Found {len(article_links)} potential article links on page")
            
            # Filter out already processed URLs
            new_links = [link for link in article_links if link not in self.processed_urls]
            logger.info(f"Processing {len(new_links)} new article links")
            
            # Process each new article
            for i, article_url in enumerate(new_links):
                try:
                    # Add to processed set immediately
                    self.processed_urls.add(article_url)
                    
                    # Create a new page for article extraction
                    article_page = await self.context.new_page()
                    article_data = await self._extract_article_data_playwright(article_page, article_url)
                    await article_page.close()
                    
                    if article_data:
                        # Check if Premier League content
                        full_text = f"{article_data['title']} {article_data['content']}"
                        if await self.is_premier_league_content(full_text):
                            # Extract entities using database data
                            entities = await self.extract_mentioned_entities(full_text)
                            article_data['teams'] = entities['teams']
                            article_data['players'] = entities['players']
                            
                            articles.append(article_data)
                            logger.info(f"Found Premier League article {i+1}/{len(new_links)}: {article_data['title'][:60]}...")
                    
                    # Rate limiting
                    if i < len(new_links) - 1:
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Error processing article {article_url}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error fetching articles from page {page_url}: {e}")
        
        return articles
    
    def _extract_article_links_enhanced(self, soup: BeautifulSoup) -> List[str]:
        """
        Enhanced article link extraction for JavaScript-rendered content.
        
        Args:
            soup: BeautifulSoup object of the rendered page
            
        Returns:
            List of article URLs
        """
        article_links = []
        
        # Enhanced selectors for JavaScript-rendered Goal.com content
        enhanced_selectors = [
            # Card-based article links (most common after JS rendering)
            'article[data-testid="card"] a[href]',
            'div[data-testid="card"] a[href]',
            '[data-testid="card-link"]',
            
            # News card structures
            '.news-card a[href*="/lists/"]',
            '.news-card a[href*="/news/"]',
            '.news-card a[href*="/blt"]',
            
            # Article cards with specific classes
            'article.card .card-title a[href]',
            'article.card .card-content a[href]',
            'article.card h3 a[href]',
            'article.card h2 a[href]',
            
            # Generic card patterns
            '.card a[href*="/en-gb/lists/"]',
            '.card a[href*="/en-gb/news/"]',
            '.card a[href*="/lists/"]',
            '.card a[href*="/news/"]',
            
            # Story card patterns (often used after JS rendering)
            '.story-card a[href]',
            '.story a[href]',
            
            # List and news article patterns
            'a[href*="/en-gb/lists/"]',
            'a[href*="/en-gb/news/"]',
            'a[href*="/lists/"]',
            'a[href*="/news/"]',
            'a[href*="/blt"]',  # Goal.com article ID pattern
            
            # Headline links
            'h1 a[href*="goal.com"]',
            'h2 a[href*="goal.com"]',
            'h3 a[href*="goal.com"]',
            
            # Data attribute selectors (common in modern JS frameworks)
            '[data-link*="/lists/"]',
            '[data-href*="/lists/"]',
            '[data-url*="/lists/"]',
        ]
        
        # Extract links using enhanced selectors
        for selector in enhanced_selectors:
            try:
                links = soup.select(selector)
                logger.debug(f"Enhanced selector '{selector}' found {len(links)} links")
                
                for link in links:
                    # Get href from various possible attributes
                    href = (link.get('href') or 
                           link.get('data-link') or 
                           link.get('data-href') or 
                           link.get('data-url') or '')
                    
                    if self._is_valid_article_link(href):
                        full_url = self._build_full_url(href)
                        if full_url not in article_links:
                            article_links.append(full_url)
                            logger.debug(f"Added article link: {full_url}")
                            
            except Exception as e:
                logger.debug(f"Error with enhanced selector '{selector}': {e}")
                continue
        
        # Additional extraction: look for JSON-LD structured data
        try:
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'url' in data:
                        url = data['url']
                        if self._is_valid_article_link(url):
                            full_url = self._build_full_url(url)
                            if full_url not in article_links:
                                article_links.append(full_url)
                                logger.debug(f"Added JSON-LD link: {full_url}")
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Error extracting JSON-LD links: {e}")
        
        # Remove duplicates while preserving order
        unique_links = []
        seen = set()
        for link in article_links:
            clean_link = link.split('#')[0].split('?')[0]
            if clean_link not in seen and len(clean_link) > 30:
                seen.add(clean_link)
                unique_links.append(link)
        
        logger.info(f"Extracted {len(unique_links)} unique valid article links")
        
        # Log sample links for debugging
        if unique_links:
            logger.debug("Sample extracted links:")
            for i, link in enumerate(unique_links[:5]):
                logger.debug(f"  {i+1}. {link}")
        
        return unique_links
    
    async def _extract_article_data_playwright(self, page: Page, url: str) -> Optional[Dict]:
        """
        Extract article data using Playwright for JavaScript-rendered content.
        
        Args:
            page: Playwright Page instance
            url: Article URL
            
        Returns:
            Dictionary containing article data or None if extraction failed
        """
        try:
            clean_url = url.split('#')[0]
            
            # Navigate to article page
            await page.goto(clean_url, wait_until='networkidle', timeout=30000)
            
            # Wait for article content to load
            try:
                await page.wait_for_selector('h1, .article-title, [data-testid="headline"]', timeout=10000)
            except Exception:
                logger.debug(f"Article title not found immediately for {clean_url}")
                await asyncio.sleep(2)  # Give it more time
            
            # Get rendered HTML
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract article components
            title = self._extract_title(soup)
            if not title:
                logger.debug(f"No title found for {clean_url}")
                return None
            
            content = self._extract_content(soup)
            if not content or len(content.strip()) < 100:
                logger.debug(f"Insufficient content for {clean_url}")
                return None
            
            published_date = self._extract_published_date(soup)
            author = self._extract_author(soup)
            
            # Validate we have meaningful data
            if len(title.strip()) < 10:
                logger.debug(f"Title too short for {clean_url}")
                return None
            
            return {
                'url': clean_url,
                'title': title.strip(),
                'content': content.strip(),
                'published_date': published_date,
                'source': self.site_name,
                'author': author
            }
            
        except Exception as e:
            logger.error(f"Error extracting article data from {url}: {e}")
            return None
    
    def _is_valid_article_link(self, href: str) -> bool:
        """Check if a link is a valid Goal.com article."""
        if not href or len(href) < 10:
            return False
        
        href_lower = href.lower()
        
        # Goal.com specific patterns
        goal_patterns = [
            '/en-gb/lists/',
        ]
        
        has_goal_pattern = any(pattern in href_lower for pattern in goal_patterns)
        if not has_goal_pattern:
            return False
        
        # Exclude non-article pages
        exclusions = [
            '/fixtures',
            '/results',
            '/tables',
            '/transfers/live',
            '/live-scores',
            '/standings',
            'javascript:',
            'mailto:',
            'tel:',
            '#',
            '/search',
            '/login',
            '/register'
        ]
        
        for exclusion in exclusions:
            if exclusion in href_lower:
                return False
        
        return True
    
    def _build_full_url(self, href: str) -> str:
        """Build full URL from href."""
        if href.startswith('http'):
            return href
        elif href.startswith('//'):
            return f"https:{href}"
        elif href.startswith('/'):
            return f"https://www.goal.com{href}"
        else:
            return f"https://www.goal.com/{href}"
    
    # Include the same extraction methods from the original crawler
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title with multiple fallbacks."""
        selectors = [
            'h1[data-testid="headline"]',
            'h1.article-title',
            '.headline h1',
            'h1.main-headline',
            '.article-header h1',
            '.post-title h1',
            'h1',
            '[data-testid="title"]',
            '.title'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text().strip()
                    title = re.sub(r'\s+', ' ', title)
                    title = re.sub(r'^.*?\|', '', title).strip()
                    
                    if title and len(title) > 10 and len(title) < 200:
                        return title
            except Exception as e:
                logger.debug(f"Error with title selector '{selector}': {e}")
                continue
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract article content with enhanced cleaning."""
        content_parts = []
        
        selectors = [
            '[data-testid="article-body"] p',
            '.article-body p',
            '.post-content p',
            '.content p',
            '.article-text p',
            'article p',
            '.entry-content p',
            '.story-body p',
            '.main-content p'
        ]
        
        for selector in selectors:
            try:
                paragraphs = soup.select(selector)
                if paragraphs:
                    potential_content = []
                    for p in paragraphs:
                        text = p.get_text().strip()
                        
                        if (text and 
                            len(text) > 15 and
                            not text.lower().startswith(('advertisement', 'subscribe', 'follow us', 'read more')) and
                            not re.match(r'^[A-Z\s]{2,}$', text) and
                            not text.count('@') > 2):
                            
                            potential_content.append(text)
                    
                    if potential_content and len(' '.join(potential_content)) > 100:
                        content_parts = potential_content
                        break
            except Exception as e:
                logger.debug(f"Error with content selector '{selector}': {e}")
                continue
        
        if not content_parts:
            try:
                paragraphs = soup.find_all('p')
                content_parts = []
                for p in paragraphs:
                    text = p.get_text().strip()
                    if (text and len(text) > 20 and 
                        'cookie' not in text.lower() and 
                        'privacy' not in text.lower() and
                        len(text) < 1000):
                        content_parts.append(text)
            except Exception as e:
                logger.debug(f"Error in fallback content extraction: {e}")
        
        content = ' '.join(content_parts)
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n+', ' ', content)
        
        return content.strip()
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract publication date."""
        selectors = [
            '[data-testid="publish-time"]',
            '.component-date[data-testid="publish-time"]',
            'time[datetime]',
            '.publish-date time',
            '.article-date time',
            '[data-testid="timestamp"]',
            '.timestamp'
        ]
        
        for selector in selectors:
            try:
                time_element = soup.select_one(selector)
                if time_element:
                    datetime_attr = time_element.get('datetime')
                    if datetime_attr:
                        date = self._parse_datetime_string(datetime_attr)
                        if date:
                            return date
                    
                    date_text = time_element.get_text().strip()
                    if date_text:
                        date = self._parse_datetime_string(date_text)
                        if date:
                            return date
            except Exception as e:
                logger.debug(f"Error with date selector '{selector}': {e}")
                continue
        
        return None
    
    def _parse_datetime_string(self, date_string: str) -> Optional[datetime]:
        """Parse datetime string."""
        if not date_string:
            return None
        
        try:
            formats_to_try = [
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S%z',
                '%d %b %Y %H:%M',
                '%B %d, %Y',
                '%d %B %Y',
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%m/%d/%Y'
            ]
            
            clean_string = date_string.strip()
            
            if '+' in clean_string and clean_string.count(':') >= 2:
                clean_string = clean_string.split('+')[0].strip()
            
            if clean_string.endswith('Z'):
                clean_string = clean_string[:-1]
            
            if 'T' in clean_string:
                try:
                    if '.' in clean_string:
                        clean_string = clean_string.split('.')[0]
                    return datetime.fromisoformat(clean_string)
                except ValueError:
                    pass
            
            for date_format in formats_to_try:
                try:
                    return datetime.strptime(clean_string, date_format)
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Failed to parse datetime '{date_string}': {e}")
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author."""
        selectors = [
            '[data-testid="article-author"] a',
            '[data-testid="author-link"] a',
            '.author-name',
            '.byline',
            '.article-author',
            '.author'
        ]
        
        for selector in selectors:
            try:
                author_element = soup.select_one(selector)
                if author_element:
                    author = author_element.get_text().strip()
                    author = re.sub(r'^(By |Author: |Written by |Reporter: )', '', author, flags=re.IGNORECASE)
                    author = re.sub(r'\s+', ' ', author)
                    
                    if author and len(author) > 1 and len(author) < 100:
                        return author
            except Exception as e:
                logger.debug(f"Error with author selector '{selector}': {e}")
                continue
        
        return None
    
    async def crawl(self) -> List[Dict]:
        """Crawl method for compatibility with test scripts."""
        return await self.fetch_articles()
    
    async def close(self):
        """Clean up resources including Playwright."""
        await super().close()
        await self._cleanup_playwright()
