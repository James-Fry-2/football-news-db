"""
Association tables for many-to-many relationships.
Keep all association tables in one place to avoid circular imports.
"""
from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey
from datetime import datetime, timezone
from ..database import Base

# Association table for Article-Player relationship
article_players = Table(
    'article_player',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('article.id', ondelete='CASCADE'), primary_key=True),
    Column('player_id', Integer, ForeignKey('player.id', ondelete='CASCADE'), primary_key=True),
    Column('mention_type', String(50)),  # e.g., 'main', 'substitute', 'transfer'
    Column('created_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
)

# Association table for Article-Team relationship
article_teams = Table(
    'article_team',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('article.id', ondelete='CASCADE'), primary_key=True),
    Column('team_id', Integer, ForeignKey('team.id', ondelete='CASCADE'), primary_key=True),
    Column('mention_type', String(50)),  # e.g., 'home', 'away', 'transfer'
    Column('created_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
)