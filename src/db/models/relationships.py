"""
Configure all relationships in one place after all models are defined.
This avoids circular imports by separating relationship definitions.
"""
from sqlalchemy.orm import relationship
from .associations import article_players, article_teams
from .article import Article
from .team import Team
from .player import Player

def configure_relationships():
    """Configure all model relationships after models are imported."""
    
    # Article relationships
    Article.players = relationship(
        "Player", 
        secondary=article_players, 
        back_populates="articles",
        lazy="select"
    )
    Article.teams = relationship(
        "Team", 
        secondary=article_teams, 
        back_populates="articles",
        lazy="select"
    )
    
    # Team relationships
    Team.articles = relationship(
        "Article", 
        secondary=article_teams, 
        back_populates="teams",
        lazy="select"
    )
    Team.players = relationship(
        "Player", 
        back_populates="team",
        lazy="select"
    )
    
    # Player relationships
    Player.articles = relationship(
        "Article", 
        secondary=article_players, 
        back_populates="players",
        lazy="select"
    )
    Player.team = relationship(
        "Team", 
        back_populates="players",
        lazy="select"
    )
