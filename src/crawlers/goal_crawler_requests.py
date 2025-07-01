"""
Goal.com Crawler with Requests

Standard Goal.com crawler that uses requests to fetch content
and extract article links from static HTML.
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import asyncio
import re
import requests

from .base_crawler import BaseCrawler
from ..db.services.article_service import ArticleService

logger = logging.getLogger(__name__)

class GoalNewsRequestsCrawler(BaseCrawler):
    """Goal News Crawler using Requests for static content."""
    
    def __init__(self, article_service: ArticleService = None, db_session: AsyncSession = None,
                 enable_user_agent_rotation: bool = True, max_pages: int = 3):
        """
        Initialize Goal.com crawler with Requests support.
        
        Args:
            article_service: Service for saving articles to database
            db_session: Database session for Premier League data
            enable_user_agent_rotation: Whether to enable user-agent rotation
            max_pages: Maximum number of pages to crawl (default: 3)
        """
        # Initialize base crawler
        super().__init__(db_session, None, enable_user_agent_rotation, None)
        
        self.article_service = article_service
        self.base_url = "https://www.goal.com/en-gb/premier-league"
        self.news_base_url = "https://www.goal.com/en-gb/premier-league/news"
        self.site_name = "Goal News"
        self.max_pages = max_pages
        
        # Track processed URLs to avoid duplicates
        self.processed_urls = set()
    
    async def fetch_articles(self) -> List[Dict]:
        """
        Fetch articles from Goal.com Premier League section using Requests.
        
        Returns:
            List of article dictionaries
        """
        # Initialize Premier League data if we have a database session
        if self.db_session:
            await self.initialize_data(self.db_session)
        
        articles = []
        
        try:
            # Skip main Premier League page and go directly to paginated news section
            # (Main page commented out to focus on specific news pagination)
            
            # Fetch articles from paginated news section
            for page_num in range(1, self.max_pages + 1):
                page_url = f"{self.news_base_url}/{page_num}/2kwbbcootiqqgmrzs6o5inle5"
                logger.info(f"Fetching Goal.com news page {page_num}: {page_url}")
                
                page_articles = await self._fetch_page_articles_requests(page_url)
                if not page_articles:
                    logger.info(f"No new articles found on page {page_num}")
                    # Still continue as Goal.com might have gaps
                    continue
                
                articles.extend(page_articles)
                logger.info(f"Found {len(page_articles)} new articles on page {page_num}")
                
                # Add delay between pages
                await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error fetching Goal.com articles with Requests: {e}")
        
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
    
    async def _fetch_page_articles_requests(self, page_url: str) -> List[Dict]:
        """
        Fetch articles from a specific Goal.com page using Requests.
        
        Args:
            page_url: URL of the page to fetch
            
        Returns:
            List of article dictionaries from this page
        """
        articles = []
        
        try:
            # Fetch the page content
            response = self.session.get(page_url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
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
                    
                    # Extract article data
                    article_data = await self._extract_article_data_requests(article_url)
                    
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
    
    async def _extract_article_data_requests(self, url: str) -> Optional[Dict]:
        """
        Extract article data using Requests.
        
        Args:
            url: Article URL
            
        Returns:
            Dictionary containing article data or None if extraction failed
        """
        try:
            clean_url = url.split('#')[0]
            
            # Fetch article page
            response = self.session.get(clean_url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
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
            
            # Handle timezone offset
            if '+' in clean_string and clean_string.count(':') >= 2:
                clean_string = clean_string.split('+')[0].strip()
            
            # Handle ISO format with 'Z' timezone indicator
            if 'T' in clean_string:
                try:
                    if '.' in clean_string:
                        clean_string = clean_string.split('.')[0]
                    
                    # If string ends with 'Z', replace with +00:00 for proper timezone parsing
                    if clean_string.endswith('Z'):
                        clean_string = clean_string[:-1] + '+00:00'
                        return datetime.fromisoformat(clean_string)
                    else:
                        # Try direct fromisoformat first
                        try:
                            return datetime.fromisoformat(clean_string)
                        except ValueError:
                            # If no timezone info, assume UTC
                            parsed_dt = datetime.fromisoformat(clean_string)
                            return parsed_dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            # Try other date formats
            for date_format in formats_to_try:
                try:
                    parsed_dt = datetime.strptime(clean_string, date_format)
                    # If no timezone info, assume UTC
                    if parsed_dt.tzinfo is None:
                        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                    return parsed_dt
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
        """Clean up resources including requests."""
        await super().close()
