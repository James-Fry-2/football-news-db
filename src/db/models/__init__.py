"""
Models package initialization - configure relationships here
"""
from .article import Article
from .team import Team
from .player import Player
from .associations import article_players, article_teams
from .relationships import configure_relationships

# Configure relationships after all models are imported
configure_relationships()

# Export all models
__all__ = [
    'Article',
    'Team', 
    'Player',
    'article_players',
    'article_teams'
]