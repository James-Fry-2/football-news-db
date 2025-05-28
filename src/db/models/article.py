from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base
from .player import article_players
from .team import article_teams

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    published_date = Column(DateTime, nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)
    author = Column(String(100))
    status = Column(String(20), default='active')  # active, archived, draft
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime)

    # Relationships
    players = relationship("Player", secondary=article_players, back_populates="articles")
    teams = relationship("Team", secondary=article_teams, back_populates="articles")

    # Indexes
    __table_args__ = (
        Index('idx_article_status_date', 'status', 'published_date'),
        Index('idx_article_source_date', 'source', 'published_date'),
    )

    def __repr__(self):
        return f"<Article(title='{self.title}', source='{self.source}')>" 