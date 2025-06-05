"""
Player model - no imports from other models
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index, ForeignKey
from datetime import datetime, timezone
from ..database import Base

class Player(Base):
    __tablename__ = "player"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    position = Column(String(50), index=True)
    nationality = Column(String(100), index=True)
    birth_date = Column(DateTime)
    team_id = Column(Integer, ForeignKey('team.id', ondelete='SET NULL'))
    status = Column(String(20), default='active')  # active, injured, retired
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime)

    # Indexes
    __table_args__ = (
        Index('idx_player_team_status', 'team_id', 'status'),
        Index('idx_player_name_nationality', 'name', 'nationality'),
    )

    def __repr__(self):
        return f"<Player(name='{self.name}', position='{self.position}')>"