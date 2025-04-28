from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging
import requests
from datetime import datetime

from src.data.premier_league_data import (
    PREMIER_LEAGUE_TEAMS,
    PREMIER_LEAGUE_PLAYERS,
    TEAM_NICKNAMES,
    PLAYER_NICKNAMES
)

logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """
    Base class for all football news crawlers.
    Provides common functionality and defines the interface that all crawlers must implement.
    """
    
    def __init__(self):
        """Initialize the crawler with a session and common data."""
        self.session = requests.Session()
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
    
    def extract_mentioned_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract mentioned teams and players from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with 'teams' and 'players' keys containing lists of mentioned entities
        """
        text_lower = text.lower()
        
        mentioned_teams = []
        mentioned_players = []
        
        # Check for team mentions
        for team in PREMIER_LEAGUE_TEAMS:
            if team.lower() in text_lower:
                mentioned_teams.append(team)
        
        # Check for player mentions
        for player in PREMIER_LEAGUE_PLAYERS:
            if player.lower() in text_lower:
                mentioned_players.append(player)
        
        return {
            'teams': mentioned_teams,
            'players': mentioned_players
        }
    
    @abstractmethod
    def crawl(self) -> List[Dict]:
        """
        Crawl the source for Premier League articles.
        
        Returns:
            List of dictionaries containing article data
        """
        pass
    
    def extract_article_data(self, url: str) -> Optional[Dict]:
        """
        Extract article data from a URL.
        
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