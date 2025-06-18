from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import aiohttp
import asyncio
import re

from .base_crawler import BaseCrawler
from ..db.services.article_service import ArticleService

logger = logging.getLogger(__name__)

class BBCCrawler(BaseCrawler):
    """Crawler for BBC Sport football articles with team-specific support."""
    
    # BBC-specific header requirements
    BBC_HEADERS = {
        'Referer': 'https://www.bbc.co.uk/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    # Premier League team URL mappings for BBC Sport
    TEAM_URLS = {
        'afc-bournemouth': 'AFC Bournemouth',
        'arsenal': 'Arsenal',
        'aston-villa': 'Aston Villa',
        'brentford': 'Brentford',
        'brighton-and-hove-albion': 'Brighton & Hove Albion',
        'burnley': 'Burnley',
        'chelsea': 'Chelsea',
        'crystal-palace': 'Crystal Palace',
        'everton': 'Everton',
        'fulham': 'Fulham',
        'leeds-united': 'Leeds United',
        'liverpool': 'Liverpool',
        'manchester-city': 'Manchester City',
        'manchester-united': 'Manchester United',
        'newcastle-united': 'Newcastle United',
        'nottingham-forest': 'Nottingham Forest',
        'sunderland': 'Sunderland',
        'tottenham-hotspur': 'Tottenham Hotspur',
        'west-ham-united': 'West Ham United',
        'wolverhampton-wanderers': 'Wolverhampton Wanderers'
    }
    
    def __init__(self, article_service: ArticleService = None, db_session: AsyncSession = None,
                 enable_user_agent_rotation: bool = True, target_team: str = None, 
                 max_pages_per_team: int = 3):
        """
        Initialize BBC crawler with site-specific headers and user-agent rotation.
        
        Args:
            article_service: Service for saving articles to database
            db_session: Database session for Premier League data
            enable_user_agent_rotation: Whether to enable user-agent rotation
            target_team: Specific team to crawl (team URL slug), None for all teams
            max_pages_per_team: Maximum number of pages to crawl per team
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
        self.target_team = target_team
        self.max_pages_per_team = max_pages_per_team
        
        # Validate target team if specified
        if self.target_team and self.target_team not in self.TEAM_URLS:
            logger.warning(f"Unknown team '{self.target_team}'. Available teams: {list(self.TEAM_URLS.keys())}")

    async def fetch_articles(self) -> List[Dict]:
        """
        Fetch articles from BBC Sport football section or specific team pages.
        
        Returns:
            List of article dictionaries
        """
        # Initialize Premier League data if we have a database session
        if self.db_session:
            await self.initialize_data(self.db_session)
        
        articles = []
        
        # Use the base crawler's method to get a properly configured session
        async with await self.get_aiohttp_session() as session:
            if self.target_team:
                # Get current Premier League teams to validate target team
                premier_league_teams = await self._get_premier_league_teams(session)
                
                if self.target_team in premier_league_teams:
                    # Crawl specific Premier League team
                    team_name = premier_league_teams[self.target_team]
                    logger.info(f"Crawling BBC Sport for Premier League team: {team_name}")
                    team_articles = await self._crawl_team_pages(session, self.target_team, premier_league_teams)
                    articles.extend(team_articles)
                else:
                    logger.warning(f"Team '{self.target_team}' is not in the current Premier League. Available teams: {list(premier_league_teams.keys())}")
                    # Still try to crawl it in case it's a valid team URL
                    logger.info(f"Attempting to crawl '{self.target_team}' anyway...")
                    team_articles = await self._crawl_team_pages(session, self.target_team)
                    articles.extend(team_articles)
            else:
                # Crawl all Premier League teams
                logger.info("Crawling BBC Sport for all Premier League teams")
                team_articles = await self._crawl_all_teams(session)
                articles.extend(team_articles)
                
                # Also crawl general football section
                general_articles = await self._crawl_general_football(session)
                articles.extend(general_articles)

        logger.info(f"Total articles collected: {len(articles)}")
        return articles

    async def _crawl_all_teams(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Crawl all Premier League teams concurrently."""
        articles = []
        
        # Get current Premier League teams dynamically
        premier_league_teams = await self._get_premier_league_teams(session)
        
        # Create tasks for all Premier League teams
        tasks = []
        for team_slug in premier_league_teams.keys():
            task = self._crawl_team_pages(session, team_slug, premier_league_teams)
            tasks.append(task)
        
        # Run tasks concurrently with a semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent team crawls
        
        async def limited_crawl(team_task):
            async with semaphore:
                return await team_task
        
        # Execute all team crawls
        team_results = await asyncio.gather(*[limited_crawl(task) for task in tasks], return_exceptions=True)
        
        # Collect results
        for result in team_results:
            if isinstance(result, Exception):
                logger.error(f"Error crawling team: {result}")
            elif isinstance(result, list):
                articles.extend(result)
        
        return articles

    async def _crawl_team_pages(self, session: aiohttp.ClientSession, team_slug: str, team_names: Dict[str, str] = None) -> List[Dict]:
        """
        Crawl a specific team's pages with pagination support.
        
        Args:
            session: aiohttp ClientSession
            team_slug: Team URL slug (e.g., 'arsenal', 'manchester-city')
            team_names: Dictionary of team names (optional, uses TEAM_URLS as fallback)
            
        Returns:
            List of article dictionaries for the team
        """
        articles = []
        # Use provided team names or fallback to static mapping
        team_name_mapping = team_names or self.TEAM_URLS
        team_name = team_name_mapping.get(team_slug, team_slug)
        
        for page_num in range(1, self.max_pages_per_team + 1):
            try:
                # Construct team page URL
                if page_num == 1:
                    team_url = f"https://www.bbc.co.uk/sport/football/teams/{team_slug}"
                else:
                    team_url = f"https://www.bbc.co.uk/sport/football/teams/{team_slug}?page={page_num}"
                
                logger.info(f"Crawling {team_name} page {page_num}: {team_url}")
                
                async with session.get(team_url) as response:
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} for {team_url}")
                        break  # Stop pagination on error
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract articles from this page
                    page_articles = await self._extract_team_page_articles(session, soup, team_name)
                    
                    if not page_articles:
                        logger.info(f"No more articles found for {team_name} on page {page_num}")
                        break  # Stop pagination if no articles found
                    
                    articles.extend(page_articles)
                    logger.info(f"Found {len(page_articles)} articles on {team_name} page {page_num}")
                    
                    # Add delay between pages to be respectful
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error crawling {team_name} page {page_num}: {e}")
                break
        
        logger.info(f"Total articles for {team_name}: {len(articles)}")
        return articles

    async def _extract_team_page_articles(self, session: aiohttp.ClientSession, soup: BeautifulSoup, team_name: str) -> List[Dict]:
        """
        Extract articles from a team page, handling both embedded articles and article links.
        
        Args:
            session: aiohttp ClientSession
            soup: BeautifulSoup object of the team page
            team_name: Name of the team for context
            
        Returns:
            List of article dictionaries
        """
        articles = []
        
        # Extract embedded articles first
        embedded_articles = self._extract_embedded_articles(soup, team_name)
        articles.extend(embedded_articles)
        
        # Extract article links and fetch their content (including links from embedded articles)
        article_links = self._extract_team_page_links(soup)
        
        # Process article links
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
                    logger.debug(f"Found linked article: {article_data['title']}")
            
            # Add small delay between article fetches
            await asyncio.sleep(0.5)
        
        return articles

    def _extract_embedded_articles(self, soup: BeautifulSoup, team_name: str) -> List[Dict]:
        """
        Extract embedded articles from team page using the provided HTML structure.
        
        Args:
            soup: BeautifulSoup object of the team page
            team_name: Name of the team for context
            
        Returns:
            List of embedded article dictionaries
        """
        articles = []
        
        # Find embedded articles using the provided selector
        embedded_articles = soup.find_all('article', {'data-testid': 'content-post'})
        
        for article_elem in embedded_articles:
            try:
                # Check if this embedded article has a link at the bottom - if so, skip it
                article_links = article_elem.find_all('a', class_=re.compile(r'.*InlineLink.*'))
                if article_links:
                    # Skip this embedded article as we'll scrape the link instead
                    logger.debug("Skipping embedded article with link - will scrape link instead")
                    continue
                
                # Extract title - get the span with role="text" and extract only the first span (title)
                title_container = article_elem.find('span', {'role': 'text'})
                if not title_container:
                    continue
                
                # Get the first span which contains the actual title (excluding timestamp)
                title_spans = title_container.find_all('span', recursive=False)
                if not title_spans:
                    continue
                
                title = title_spans[0].get_text().strip()
                
                # Extract published date from accessible-timestamp
                published_date = None
                accessible_timestamp = article_elem.find('span', {'data-testid': 'accessible-timestamp'})
                if accessible_timestamp:
                    date_text = accessible_timestamp.get_text().strip()
                    try:
                        # Parse "published at 09:22 16 June" format
                        if 'published at' in date_text:
                            date_part = date_text.replace('published at', '').strip()
                            published_date = self._parse_bbc_date(date_part)
                    except Exception as e:
                        logger.debug(f"Could not parse date '{date_text}': {e}")
                
                # Extract author - look for "Contributor" in class name
                author_elem = article_elem.find(attrs={'class': re.compile(r'.*Contributor.*')})
                author = None
                if author_elem:
                    author_text = author_elem.get_text().strip()
                    # Extract just the name (before any line breaks or additional info)
                    if '\n' in author_text:
                        author = author_text.split('\n')[0]
                    else:
                        author = author_text
                    # Remove "strong" tags content if present
                    if author:
                        author = re.sub(r'<[^>]+>', '', author).strip()
                
                # Extract content from paragraphs
                content_paragraphs = article_elem.find_all('p', class_=re.compile(r'ssrcss-.*-Paragraph'))
                content_parts = []
                for p in content_paragraphs:
                    # Skip contributor paragraphs
                    if 'Contributor' in ' '.join(p.get('class', [])):
                        continue
                    text = p.get_text().strip()
                    if text:
                        content_parts.append(text)
                
                content = ' '.join(content_parts)
                
                # Ensure we have a clean title and content
                if title and content and len(title) > 0:
                    article_data = {
                        'title': title,
                        'content': content,
                        'url': f"embedded_article_{hash(title)}",  # Generate unique identifier
                        'published_date': published_date,
                        'source': self.site_name,
                        'author': author
                    }
                    
                    articles.append(article_data)
                    logger.debug(f"Extracted embedded article: {title}")
                
            except Exception as e:
                logger.error(f"Error extracting embedded article: {e}")
                continue
        
        return articles

    def _extract_team_page_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract article links from team page, including links from embedded articles.
        
        Args:
            soup: BeautifulSoup object of the team page
            
        Returns:
            List of article URLs
        """
        article_links = []
        
        # First, extract links from embedded articles that have InlineLink elements
        embedded_articles = soup.find_all('article', {'data-testid': 'content-post'})
        for article_elem in embedded_articles:
            inline_links = article_elem.find_all('a', class_=re.compile(r'.*InlineLink.*'))
            for link in inline_links:
                href = link.get('href', '')
                if self._is_valid_team_article_link(href):
                    full_url = self._build_full_url(href)
                    if full_url not in article_links:
                        article_links.append(full_url)
                        logger.debug(f"Found embedded article link: {full_url}")
        
        # Then look for other BBC Sport article links
        article_link_selectors = [
            'a[href*="/sport/football/articles/"]',
            'a[href*="/sport/football/"]',
        ]
        
        for selector in article_link_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href', '')
                if self._is_valid_team_article_link(href):
                    full_url = self._build_full_url(href)
                    if full_url not in article_links:
                        article_links.append(full_url)
        
        logger.debug(f"Found {len(article_links)} article links on team page")
        return article_links

    def _is_valid_team_article_link(self, href: str) -> bool:
        """
        Check if a link is a valid BBC Sport football article from team page.
        
        Args:
            href: The href attribute from the link
            
        Returns:
            True if the link appears to be a football article
        """
        if not href:
            return False
        
        # Must be a football-related link
        if '/sport/football/' not in href:
            return False
        
        # Exclude URLs with fragments (e.g., #comments)
        if '#' in href:
            return False
        
        # Include specific article patterns
        valid_patterns = [
            '/sport/football/articles/',  # New article format
            '/sport/football/[0-9]',      # Legacy article format
        ]
        
        # Check if matches any valid pattern
        for pattern in valid_patterns:
            if pattern in href or re.search(pattern.replace('[0-9]', r'\d'), href):
                return True
        
        # Exclude non-article pages
        exclusions = [
            '/football/teams/',     # Team directory pages
            '/football/tables',     # League tables
            '/football/fixtures',   # Fixture lists
            '/football/results',    # Results pages
            '/football/live',       # Live pages
            '/football?',           # Query-only pages
        ]
        
        for exclusion in exclusions:
            if exclusion in href:
                return False
        
        return False  # Default to false for safety

    def _parse_bbc_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse BBC-style date strings.
        
        Args:
            date_text: Date text like "19:10 10 June", "10 June", or just "19:10" (today)
            
        Returns:
            datetime object or None
        """
        try:
            date_text = date_text.strip()
            
            # Check if it's just a time (like "19:10" or "06:54") - meaning today
            time_only_pattern = r'^\d{1,2}:\d{2}$'
            if re.match(time_only_pattern, date_text):
                # Parse as today's date with the given time
                today = datetime.now().date()
                time_parts = date_text.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                return datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            
            # Handle full date with time: "19:10 10 June"
            if ' ' in date_text:
                parts = date_text.strip().split()
                if len(parts) >= 2:
                    # Take last two parts as day and month
                    day_month = ' '.join(parts[-2:])
                else:
                    day_month = date_text
            else:
                day_month = date_text
            
            # Parse "10 June" format - assume current year
            current_year = datetime.now().year
            date_str = f"{day_month} {current_year}"
            
            return datetime.strptime(date_str, '%d %B %Y')
            
        except Exception as e:
            logger.debug(f"Could not parse BBC date '{date_text}': {e}")
            return None

    async def _crawl_general_football(self, session: aiohttp.ClientSession) -> List[Dict]:
        """
        Crawl general BBC Sport football section (fallback to original method).
        
        Args:
            session: aiohttp ClientSession
            
        Returns:
            List of article dictionaries
        """
        articles = []
        
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

    @classmethod
    def get_available_teams(cls) -> Dict[str, str]:
        """Get available team slugs and names."""
        return cls.TEAM_URLS.copy()

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
        
        # Exclude URLs with fragments (e.g., #comments)
        if '#' in href:
            return False
        
        # Exclude certain types of pages
        exclusions = [
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
        Build full URL from href and strip any fragments.
        
        Args:
            href: Relative or absolute URL
            
        Returns:
            Full URL without fragments
        """
        # Strip fragment (everything after #) first
        if '#' in href:
            href = href.split('#')[0]
        
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
            # Strip URL fragment before making request and storing
            clean_url = url.split('#')[0] if '#' in url else url
            
            async with session.get(clean_url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {clean_url}")
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract article components
                title = self._extract_title(soup)
                content = self._extract_content(soup)
                published_date = self._extract_published_date(soup)
                author = self._extract_author(soup)
                
                if not all([title, content]):
                    logger.warning(f"Missing essential data for {clean_url}")
                    return None
                
                return {
                    'url': clean_url,
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
            # New BBC byline format with TextContributorName class
            '[class*="TextContributorName"]',
            # Other existing selectors
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

    async def _get_premier_league_teams(self, session: aiohttp.ClientSession) -> Dict[str, str]:
        """
        Dynamically extract Premier League teams from BBC Sport Premier League page.
        
        Args:
            session: aiohttp ClientSession
            
        Returns:
            Dictionary mapping team URL slugs to team names for Premier League teams only
        """
        premier_league_teams = {}
        premier_league_url = "https://www.bbc.co.uk/sport/football/premier-league"
        
        try:
            async with session.get(premier_league_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch BBC Premier League page: {response.status}")
                    return self.TEAM_URLS  # Fallback to static list
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for team links in the format: /sport/football/teams/{team}
                team_links = soup.find_all('a', href=re.compile(r'^/sport/football/teams/[^/]+$'))
                
                for link in team_links:
                    href = link.get('href', '')
                    
                    # Extract team name from the link text
                    # Look for PromoHeadline or just get the text content
                    team_name_elem = link.find(class_=re.compile(r'.*PromoHeadline.*'))
                    if team_name_elem:
                        team_name = team_name_elem.get_text().strip()
                    else:
                        # Fallback to getting all text from the link
                        team_name = link.get_text().strip()
                    
                    # Extract team slug from URL: /sport/football/teams/arsenal -> arsenal
                    if '/sport/football/teams/' in href:
                        team_slug = href.split('/sport/football/teams/')[-1]
                        if team_name and team_slug:
                            premier_league_teams[team_slug] = team_name
                            logger.debug(f"Found Premier League team: {team_slug} -> {team_name}")
                
                logger.info(f"Extracted {len(premier_league_teams)} Premier League teams from BBC Premier League page")
                
                # If we didn't find any teams, fall back to static list
                if not premier_league_teams:
                    logger.warning("No Premier League teams found, using static fallback list")
                    return self.TEAM_URLS
                
                return premier_league_teams
                
        except Exception as e:
            logger.error(f"Error extracting Premier League teams: {e}")
            return self.TEAM_URLS  # Fallback to static list