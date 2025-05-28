from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from ..database import Base

# Association table for many-to-many relationship between articles and players
article_players = Table(
    'article_players',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id', ondelete='CASCADE'), primary_key=True),
    Column('player_id', Integer, ForeignKey('players.id', ondelete='CASCADE'), primary_key=True),
    Column('mention_type', String(50)),  # e.g., 'main', 'substitute', 'transfer'
    Column('created_at', DateTime, default=lambda: datetime.now(UTC))
)

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    position = Column(String(50), index=True)
    nationality = Column(String(100), index=True)
    birth_date = Column(DateTime)
    team_id = Column(Integer, ForeignKey('teams.id', ondelete='SET NULL'))
    status = Column(String(20), default='active')  # active, injured, retired
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    deleted_at = Column(DateTime)

    # Relationships
    articles = relationship("Article", secondary=article_players, back_populates="players")
    team = relationship("Team", back_populates="players")

    # Indexes
    __table_args__ = (
        Index('idx_player_team_status', 'team_id', 'status'),
        Index('idx_player_name_nationality', 'name', 'nationality'),
    )

    def __repr__(self):
        return f"<Player(name='{self.name}', position='{self.position}')>" 