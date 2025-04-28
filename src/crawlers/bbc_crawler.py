import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
from datetime import datetime
import logging
from src.data.premier_league_data import (
    PREMIER_LEAGUE_TEAMS,
    PREMIER_LEAGUE_PLAYERS,
    TEAM_NICKNAMES,
    PLAYER_NICKNAMES
)
from src.crawlers.base_crawler import BaseCrawler
from ..db.services.article_service import ArticleService
import aiohttp
from loguru import logger

logger = logging.getLogger(__name__)

class BBCCrawler(BaseCrawler):
    """Crawler for BBC Sport football articles."""
    
    def __init__(self, article_service: ArticleService):
        super().__init__(article_service)
        self.base_url = "https://www.bbc.co.uk/sport/football"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Create a comprehensive list of team names including nicknames
        self.all_team_names = []
        for team in PREMIER_LEAGUE_TEAMS:
            self.all_team_names.append(team.lower())
            if team in TEAM_NICKNAMES:
                for nickname in TEAM_NICKNAMES[team]:
                    self.all_team_names.append(nickname.lower())
        
        # Create a comprehensive list of player names including nicknames
        self.all_player_names = []
        for player in PREMIER_LEAGUE_PLAYERS:
            self.all_player_names.append(player.lower())
            if player in PLAYER_NICKNAMES:
                for nickname in PLAYER_NICKNAMES[player]:
                    self.all_player_names.append(nickname.lower())

    def is_premier_league_content(self, text: str) -> bool:
        """Check if the content is related to Premier League teams or players."""
        text_lower = text.lower()
        
        # Check for team names
        if any(team_name in text_lower for team_name in self.all_team_names):
            return True
            
        # Check for player names
        if any(player_name in text_lower for player_name in self.all_player_names):
            return True
            
        return False

    async def fetch_articles(self) -> List[Dict]:
        """
        Fetch articles from BBC Sport football section.
        
        Returns:
            List of article dictionaries
        """
        articles = []
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(self.base_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch BBC Sport: {response.status}")
                        return articles

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find all article links
                    article_links = soup.find_all('a', href=True)
                    for link in article_links:
                        href = link.get('href', '')
                        if '/sport/football/' in href and not href.endswith('/football'):
                            article_url = f"https://www.bbc.co.uk{href}" if href.startswith('/') else href
                            
                            # Fetch and process individual article
                            article_data = await self.extract_article_data(session, article_url)
                            if article_data and self.is_premier_league_content(article_data['content']):
                                articles.append(article_data)
                                logger.info(f"Found Premier League article: {article_data['title']}")

            except Exception as e:
                logger.error(f"Error fetching BBC Sport articles: {e}")

        return articles

    async def extract_article_data(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
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
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract article data
                title = soup.find('h1').text.strip() if soup.find('h1') else None
                content = ' '.join([p.text.strip() for p in soup.find_all('p')])
                published_date = None
                
                # Try to find publication date
                time_element = soup.find('time')
                if time_element and time_element.get('datetime'):
                    published_date = datetime.fromisoformat(time_element['datetime'].replace('Z', '+00:00'))
                
                if not all([title, content, published_date]):
                    return None

                # Extract mentioned teams and players
                entities = self.extract_mentioned_entities(content)
                
                return {
                    'url': url,
                    'title': title,
                    'content': content,
                    'published_date': published_date,
                    'source': 'BBC Sport',
                    'teams': entities['teams'],
                    'players': entities['players']
                }

        except Exception as e:
            logger.error(f"Error extracting article data from {url}: {e}")
            return None 