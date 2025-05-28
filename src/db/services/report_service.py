from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.article import Article
from ..models.player import Player
from ..models.team import Team

class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_player_articles(self, player_name: str):
        """Get all articles mentioning a specific player."""
        query = (
            select(Article)
            .join(Article.players)
            .where(Player.name == player_name)
            .order_by(Article.published_date.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_team_articles(self, team_name: str):
        """Get all articles mentioning a specific team."""
        query = (
            select(Article)
            .join(Article.teams)
            .where(Team.name == team_name)
            .order_by(Article.published_date.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_players_by_team(self, team_name: str):
        """Get all players from a specific team."""
        query = (
            select(Player)
            .join(Player.team)
            .where(Team.name == team_name)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_article_count_by_source(self):
        """Get the count of articles by source."""
        query = (
            select(Article.source, func.count(Article.id).label('count'))
            .group_by(Article.source)
        )
        result = await self.session.execute(query)
        return result.all()

    async def get_most_mentioned_players(self, limit: int = 10):
        """Get the most mentioned players across all articles."""
        query = (
            select(Player.name, func.count(Article.id).label('mention_count'))
            .join(Article.players)
            .group_by(Player.name)
            .order_by(func.count(Article.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.all()

    async def get_articles_by_date_range(self, start_date, end_date):
        """Get articles published within a date range."""
        query = (
            select(Article)
            .where(Article.published_date.between(start_date, end_date))
            .order_by(Article.published_date.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all() 