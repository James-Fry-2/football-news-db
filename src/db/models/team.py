from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from ..database import Base

# Association table for many-to-many relationship between articles and teams
article_teams = Table(
    'article_teams',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id', ondelete='CASCADE'), primary_key=True),
    Column('team_id', Integer, ForeignKey('teams.id', ondelete='CASCADE'), primary_key=True),
    Column('mention_type', String(50)),  # e.g., 'home', 'away', 'transfer'
    Column('created_at', DateTime, default=lambda: datetime.now(UTC))
)

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    league = Column(String(100), index=True)
    country = Column(String(100), index=True)
    founded_year = Column(Integer)
    status = Column(String(20), default='active')  # active, dissolved, renamed
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    deleted_at = Column(DateTime)

    # Relationships
    articles = relationship("Article", secondary=article_teams, back_populates="teams")
    players = relationship("Player", back_populates="team")

    # Indexes
    __table_args__ = (
        Index('idx_team_league_country', 'league', 'country'),
        Index('idx_team_status', 'status'),
    )

    def __repr__(self):
        return f"<Team(name='{self.name}', league='{self.league}')>" 