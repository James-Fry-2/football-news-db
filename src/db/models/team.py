"""
Team model - no imports from other models
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index
from datetime import datetime, timezone
from ..database import Base

class Team(Base):
    __tablename__ = "team"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    league = Column(String(100), index=True)
    country = Column(String(100), index=True)
    founded_year = Column(Integer, nullable=True)
    status = Column(String(20), default='active')  # active, dissolved, renamed
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_team_league_country', 'league', 'country'),
        Index('idx_team_status', 'status'),
    )

    def __repr__(self):
        return f"<Team(name='{self.name}', league='{self.league}')>"