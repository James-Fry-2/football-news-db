from typing import List, Optional, Dict
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from loguru import logger
from ..models import Article, Player, Team

class ArticleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_duplicate(self, url: str) -> bool:
        query = select(Article).where(Article.url == url)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def save_article(self, article_data: Dict) -> Optional[Article]:
        try:
            if await self.is_duplicate(article_data["url"]):
                logger.info(f"Duplicate article found: {article_data['url']}")
                return None
            
            # Prepare article data with fallback for published_date
            article_dict = {k: v for k, v in article_data.items() 
                           if k not in ['teams', 'players']}
            
            # Ensure published_date is not None (database constraint)
            if article_dict.get('published_date') is None:
                article_dict['published_date'] = datetime.now(timezone.utc)
                logger.warning(f"No published_date found for article '{article_data.get('title', 'Unknown')}', using current time")
            
            # Create article
            article = Article(**article_dict)
            self.session.add(article)
            
            # Handle team relationships
            if 'teams' in article_data:
                for team_name in article_data['teams']:
                    team = await self._get_or_create_team(team_name)
                    article.teams.append(team)
            
            # Handle player relationships  
            if 'players' in article_data:
                for player_name in article_data['players']:
                    player = await self._get_or_create_player(player_name)
                    article.players.append(player)
            
            await self.session.commit()
            await self.session.refresh(article)
            try:
                from src.tasks.vector_tasks import process_single_article_task
                process_single_article_task.delay(article.id)
                logger.info(f"📋 Queued article {article.id} for vector processing")
            except ImportError:
                # Vector processing not set up yet - gracefully continue
                logger.debug("Vector processing not available yet")
            except Exception as e:
                # Don't fail article saving if queue fails
                logger.warning(f"Failed to queue article for vector processing: {e}")
            
            return article
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error saving article: {e}")
            return None

    async def _get_or_create_team(self, team_name: str) -> Team:
        """Get existing team or create new one."""
        query = select(Team).where(Team.name == team_name)
        result = await self.session.execute(query)
        team = result.scalar_one_or_none()
        
        if not team:
            team = Team(name=team_name)
            self.session.add(team)
            await self.session.flush()  # Get ID without committing
        
        return team

    async def _get_or_create_player(self, player_name: str) -> Player:
        """Get existing player or create new one."""
        query = select(Player).where(Player.name == player_name)
        result = await self.session.execute(query)
        player = result.scalar_one_or_none()
        
        if not player:
            player = Player(name=player_name)
            self.session.add(player)
            await self.session.flush()  # Get ID without committing
        
        return player

    async def get_articles_with_relationships(
        self,
        skip: int = 0,
        limit: int = 10,
        source: Optional[str] = None
    ) -> List[Article]:
        """Get articles with their related teams and players loaded."""
        query = select(Article).options(
            selectinload(Article.teams),
            selectinload(Article.players)
        )
        
        if source:
            query = query.where(Article.source == source)
        
        query = query.offset(skip).limit(limit).order_by(Article.published_date.desc())
        result = await self.session.execute(query)
        return result.scalars().all()