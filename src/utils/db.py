"""
Database utility module for PostgreSQL operations using SQLAlchemy.
"""

from typing import Dict, List
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, UTC

from src.config.db_config import DATABASE_URL
from src.db.database import Database
from src.db.models.article import Article
from src.db.models.player import Player
from src.db.models.team import Team

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        """Initialize database connection."""
        self.session = None
    
    async def connect(self):
        """Connect to the database."""
        try:
            await Database.connect_db(DATABASE_URL)
            self.session = await Database.get_session()
            logger.info("Successfully connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise
    
    async def insert_articles(self, articles: List[Dict]) -> None:
        """
        Insert articles into the database.
        
        Args:
            articles: List of article dictionaries to insert
        """
        if not self.session:
            await self.connect()
            
        try:
            for article_data in articles:
                # Check if article already exists
                query = select(Article).where(Article.url == article_data['url'])
                result = await self.session.execute(query)
                existing_article = result.scalar_one_or_none()
                
                if existing_article:
                    # Update existing article
                    for key, value in article_data.items():
                        setattr(existing_article, key, value)
                    existing_article.updated_at = datetime.now(UTC)
                else:
                    # Create new article
                    article = Article(**article_data)
                    self.session.add(article)
                
                # Process players and teams if present
                if 'players' in article_data:
                    await self._process_players(article_data['players'], existing_article or article)
                
                if 'teams' in article_data:
                    await self._process_teams(article_data['teams'], existing_article or article)
            
            await self.session.commit()
            logger.info(f"Successfully processed {len(articles)} articles")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to insert articles: {str(e)}")
            raise
    
    async def _process_players(self, player_names: List[str], article: Article):
        """Process players mentioned in an article."""
        for player_name in player_names:
            # Check if player exists
            query = select(Player).where(Player.name == player_name)
            result = await self.session.execute(query)
            player = result.scalar_one_or_none()
            
            if not player:
                player = Player(name=player_name)
                self.session.add(player)
            
            # Add relationship if not exists
            if player not in article.players:
                article.players.append(player)
    
    async def _process_teams(self, team_names: List[str], article: Article):
        """Process teams mentioned in an article."""
        for team_name in team_names:
            # Check if team exists
            query = select(Team).where(Team.name == team_name)
            result = await self.session.execute(query)
            team = result.scalar_one_or_none()
            
            if not team:
                team = Team(name=team_name)
                self.session.add(team)
            
            # Add relationship if not exists
            if team not in article.teams:
                article.teams.append(team)
    
    async def close(self) -> None:
        """Close the database connection."""
        try:
            if self.session:
                await self.session.close()
            await Database.close_db()
            logger.info("Closed PostgreSQL connection")
        except Exception as e:
            logger.error(f"Error closing PostgreSQL connection: {str(e)}")
            raise 