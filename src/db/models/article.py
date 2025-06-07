"""
Article model - no imports from other models
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index, JSON, Float
from datetime import datetime, timezone
from ..database import Base

class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    published_date = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)
    author = Column(String(100))
    status = Column(String(20), default='active')  # active, archived, draft
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Vector-related fields
    vector_embedding = Column(JSON)
    embedding_status = Column(String(20), default='pending')  # pending, processing, completed, failed
    sentiment_score = Column(Float)
    search_vector_id = Column(String(100), index=True)
    content_hash = Column(String(64), index=True)

    # Indexes
    __table_args__ = (
        Index('idx_article_status_date', 'status', 'published_date'),
        Index('idx_article_source_date', 'source', 'published_date'),
        Index('idx_article_embedding_status', 'embedding_status'),
        Index('idx_article_sentiment', 'sentiment_score'),
    )

    def __repr__(self):
        return f"<Article(title='{self.title}', source='{self.source}')>"
