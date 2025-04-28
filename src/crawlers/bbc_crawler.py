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

logger = logging.getLogger(__name__)

class BBCCrawler(BaseCrawler):
    BASE_URL = "https://www.bbc.co.uk/sport/football/premier-league"
    
    def __init__(self):
        super().__init__()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
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

    def extract_article_data(self, url: str) -> Optional[Dict]:
        """Extract article data from a BBC Sport article page."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('h1')
            if not title:
                return None
            title = title.text.strip()
            
            # Extract content
            article_body = soup.find('article')
            if not article_body:
                return None
                
            content = ' '.join([p.text.strip() for p in article_body.find_all('p')])
            
            # Extract publication date
            date_element = soup.find('time')
            published_date = None
            if date_element and date_element.get('datetime'):
                published_date = datetime.fromisoformat(date_element['datetime'].replace('Z', '+00:00'))
            
            # Extract teams and players mentioned in the article
            full_text = f"{title} {content}"
            entities = self.extract_mentioned_entities(full_text)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'published_date': published_date,
                'source': 'BBC Sport',
                'mentioned_teams': entities['teams'],
                'mentioned_players': entities['players']
            }
            
        except Exception as e:
            logger.error(f"Error extracting article data from {url}: {str(e)}")
            return None

    def crawl(self) -> List[Dict]:
        """Crawl BBC Sport football section for Premier League articles."""
        articles = []
        try:
            response = self.session.get(self.BASE_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all article links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Check if it's an article link
                if 'article' in href and href.startswith('/'):
                    full_url = f"https://www.bbc.co.uk{href}"
                    
                    # Get the link text and surrounding content to check if it's Premier League related
                    link_text = link.get_text().strip()
                    parent_text = link.parent.get_text().strip()
                    
                    if self.is_premier_league_content(link_text) or self.is_premier_league_content(parent_text):
                        article_data = self.extract_article_data(full_url)
                        if article_data:
                            articles.append(article_data)
                            logger.info(f"Successfully crawled article: {article_data['title']}")
            
        except Exception as e:
            logger.error(f"Error crawling BBC Sport: {str(e)}")
        
        return articles 