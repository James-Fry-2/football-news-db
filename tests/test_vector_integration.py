"""
Integration tests for VectorService.

These tests use a real database (SQLite in memory) but mock external services
to test the complete workflow without requiring API keys.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.db.models.article import Article
from src.db.database import Base
from src.db.services.vector_service import VectorService


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False  # Set to True for SQL debugging
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def sample_articles(test_session):
    """Create sample articles in the test database."""
    articles = [
        Article(
            title="Manchester City Win Premier League",
            url="https://example.com/city-win",
            content="Manchester City secured the Premier League title with an excellent performance. Haaland scored twice in a brilliant victory.",
            published_date=datetime.now(timezone.utc),
            source="BBC Sport",
            embedding_status='pending'
        ),
        Article(
            title="Arsenal Transfer News",
            url="https://example.com/arsenal-transfer", 
            content="Arsenal are looking to sign new players this summer. The transfer window brings exciting possibilities.",
            published_date=datetime.now(timezone.utc),
            source="Sky Sports",
            embedding_status='pending'
        ),
        Article(
            title="Liverpool Injury Update",
            url="https://example.com/liverpool-injury",
            content="Liverpool face injury concerns ahead of the crucial match. Several key players are sidelined with various problems.",
            published_date=datetime.now(timezone.utc),
            source="ESPN",
            embedding_status='failed'  # Previously failed
        )
    ]
    
    for article in articles:
        test_session.add(article)
    
    await test_session.commit()
    
    # Refresh to get IDs
    for article in articles:
        await test_session.refresh(article)
    
    return articles


class TestVectorServiceIntegration:
    """Integration tests for VectorService with real database."""
    
    @pytest.mark.asyncio
    async def test_full_article_processing_pipeline(self, test_session, sample_articles):
        """Test complete article processing pipeline."""
        with patch('src.db.services.vector_service.openai.AsyncOpenAI'), \
             patch('src.db.services.vector_service.Pinecone'), \
             patch('src.db.services.vector_service.validate_ai_config'):
            
            # Setup VectorService with mocked externals
            service = VectorService(test_session)
            service.index = MagicMock()
            
            # Mock successful embedding generation
            mock_embedding = [0.1] * 1536
            service.generate_embedding = AsyncMock(return_value=mock_embedding)
            service.store_vector_in_pinecone = AsyncMock(return_value=True)
            
            # Get the first article
            article = sample_articles[0]
            original_id = article.id
            
            # Process the article
            success, message = await service.process_single_article(article.id)
            
            # Verify processing success
            assert success is True
            assert "Successfully processed" in message
            
            # Refresh article from database to see updates
            await test_session.refresh(article)
            
            # Verify database changes
            assert article.embedding_status == 'completed'
            assert article.vector_embedding == mock_embedding
            assert article.sentiment_score is not None
            assert article.content_hash is not None
            assert article.search_vector_id == f"article_{original_id}"
            assert article.updated_at is not None
            
            # Verify sentiment analysis
            # Article has positive words like "excellent", "brilliant"
            assert article.sentiment_score > 0
    
    @pytest.mark.asyncio
    async def test_batch_processing_with_database(self, test_session, sample_articles):
        """Test batch processing with real database operations."""
        with patch('src.db.services.vector_service.openai.AsyncOpenAI'), \
             patch('src.db.services.vector_service.Pinecone'), \
             patch('src.db.services.vector_service.validate_ai_config'):
            
            service = VectorService(test_session)
            service.index = MagicMock()
            
            # Mock successful processing for first two, failure for third
            mock_embedding = [0.2] * 1536
            service.generate_embedding = AsyncMock(return_value=mock_embedding)
            service.store_vector_in_pinecone = AsyncMock(return_value=True)
            
            # Get pending articles
            pending_ids = await service.get_pending_articles(limit=10)
            
            # Should find 3 articles (2 'pending' + 1 'failed')
            expected_pending = [a.id for a in sample_articles if a.embedding_status in ['pending', 'failed']]
            assert set(pending_ids) == set(expected_pending)
            assert len(pending_ids) == 3
            
            # Process articles sequentially to avoid session conflicts in tests
            stats = {"processed": 0, "succeeded": 0, "failed": 0, "messages": []}
            
            for article_id in pending_ids:
                success, message = await service.process_single_article(article_id)
                stats["processed"] += 1
                
                if success:
                    stats["succeeded"] += 1
                else:
                    stats["failed"] += 1
                    
                stats["messages"].append(f"Article {article_id}: {message}")
            
            # Verify batch statistics
            assert stats["processed"] == 3
            assert stats["succeeded"] == 3
            assert stats["failed"] == 0
            
            # Verify all pending articles are now completed
            for article_id in pending_ids:
                await test_session.refresh(next(a for a in sample_articles if a.id == article_id))
            
            completed_articles = [a for a in sample_articles if a.id in pending_ids]
            for article in completed_articles:
                assert article.embedding_status == 'completed'
                assert article.vector_embedding == mock_embedding
    
    @pytest.mark.asyncio
    async def test_processing_stats_with_database(self, test_session, sample_articles):
        """Test processing statistics with real database."""
        with patch('src.db.services.vector_service.openai.AsyncOpenAI'), \
             patch('src.db.services.vector_service.Pinecone'), \
             patch('src.db.services.vector_service.validate_ai_config'):
            
            service = VectorService(test_session)
            
            # Get initial stats
            stats = await service.get_processing_stats()
            
            # Verify initial state
            assert stats["pending"] == 2  # Two articles with 'pending' status
            assert stats["failed"] == 1   # One article with 'failed' status
            assert stats["completed"] == 0
            assert stats["processing"] == 0
            assert stats["total"] == 3
    
    @pytest.mark.asyncio
    async def test_reset_processing_status_with_database(self, test_session):
        """Test resetting processing status with real database."""
        with patch('src.db.services.vector_service.openai.AsyncOpenAI'), \
             patch('src.db.services.vector_service.Pinecone'), \
             patch('src.db.services.vector_service.validate_ai_config'):
            
            # Create an article stuck in processing
            stuck_article = Article(
                title="Stuck Article",
                url="https://example.com/stuck",
                content="This article is stuck in processing.",
                published_date=datetime.now(timezone.utc),
                source="Test Source",
                embedding_status='processing'  # Stuck state
            )
            test_session.add(stuck_article)
            await test_session.commit()
            await test_session.refresh(stuck_article)
            
            service = VectorService(test_session)
            
            # Reset processing status
            reset_count = await service.reset_processing_status()
            
            # Verify reset
            assert reset_count == 1
            
            # Refresh article and verify status change
            await test_session.refresh(stuck_article)
            assert stuck_article.embedding_status == 'pending'
    
    @pytest.mark.asyncio
    async def test_content_hash_deduplication(self, test_session):
        """Test content hash-based deduplication."""
        with patch('src.db.services.vector_service.openai.AsyncOpenAI'), \
             patch('src.db.services.vector_service.Pinecone'), \
             patch('src.db.services.vector_service.validate_ai_config'):
            
            # Create article that's already processed
            content = "This is test content for hashing."
            article = Article(
                title="Test Hash Article",
                url="https://example.com/hash-test",
                content=content,
                published_date=datetime.now(timezone.utc),
                source="Test Source",
                embedding_status='completed',
                vector_embedding=[0.5] * 1536,
                content_hash="existing_hash"
            )
            test_session.add(article)
            await test_session.commit()
            await test_session.refresh(article)
            
            service = VectorService(test_session)
            service.index = MagicMock()
            
            # Mock the embedding generation to avoid OpenAI calls
            service.generate_embedding = AsyncMock(return_value=[0.5] * 1536)
            service.store_vector_in_pinecone = AsyncMock(return_value=True)
            
            # Calculate what the hash should be
            expected_hash = service._generate_content_hash(f"{article.title}\n\n{article.content}")
            
            # Update article with correct hash
            article.content_hash = expected_hash
            await test_session.commit()
            
            # Try to process the same article again
            success, message = await service.process_single_article(article.id)
            
            # Should skip processing due to same content hash
            assert success is True
            assert "already processed with same content" in message
    
    @pytest.mark.asyncio 
    async def test_error_handling_with_database_rollback(self, test_session):
        """Test error handling and database rollback on failures."""
        with patch('src.db.services.vector_service.openai.AsyncOpenAI'), \
             patch('src.db.services.vector_service.Pinecone'), \
             patch('src.db.services.vector_service.validate_ai_config'):
            
            # Create test article
            article = Article(
                title="Error Test Article",
                url="https://example.com/error-test",
                content="This will cause an error.",
                published_date=datetime.now(timezone.utc),
                source="Test Source",
                embedding_status='pending'
            )
            test_session.add(article)
            await test_session.commit()
            await test_session.refresh(article)
            
            service = VectorService(test_session)
            service.index = MagicMock()
            
            # Mock embedding generation failure
            service.generate_embedding = AsyncMock(side_effect=Exception("OpenAI API error"))
            
            # Process article (should fail)
            success, message = await service.process_single_article(article.id)
            
            # Verify failure handling
            assert success is False
            assert "Failed to generate embedding" in message
            
            # Refresh and verify status was updated to failed
            await test_session.refresh(article)
            assert article.embedding_status == 'failed'
            assert article.vector_embedding is None
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_integration(self, test_session):
        """Test sentiment analysis with real database storage."""
        with patch('src.db.services.vector_service.openai.AsyncOpenAI'), \
             patch('src.db.services.vector_service.Pinecone'), \
             patch('src.db.services.vector_service.validate_ai_config'):
            
            # Create articles with different sentiments
            articles = [
                Article(
                    title="Amazing Victory",
                    url="https://example.com/positive",
                    content="Amazing victory! Excellent performance and brilliant goals. The team was outstanding and fantastic.",
                    published_date=datetime.now(timezone.utc),
                    source="Test Source",
                    embedding_status='pending'
                ),
                Article(
                    title="Terrible Defeat", 
                    url="https://example.com/negative",
                    content="Terrible defeat and awful performance. Complete disaster with poor defending and bad decisions.",
                    published_date=datetime.now(timezone.utc),
                    source="Test Source",
                    embedding_status='pending'
                ),
                Article(
                    title="Match Report",
                    url="https://example.com/neutral",
                    content="The match was played today. Both teams participated in the fixture.",
                    published_date=datetime.now(timezone.utc),
                    source="Test Source", 
                    embedding_status='pending'
                )
            ]
            
            for article in articles:
                test_session.add(article)
            await test_session.commit()
            
            for article in articles:
                await test_session.refresh(article)
            
            service = VectorService(test_session)
            service.index = MagicMock()
            
            # Mock successful processing
            service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
            service.store_vector_in_pinecone = AsyncMock(return_value=True)
            
            # Process all articles
            for article in articles:
                success, _ = await service.process_single_article(article.id)
                assert success is True
                await test_session.refresh(article)
            
            # Verify sentiment scores
            positive_article = articles[0]
            negative_article = articles[1] 
            neutral_article = articles[2]
            
            assert positive_article.sentiment_score > 0  # Positive sentiment
            assert negative_article.sentiment_score < 0  # Negative sentiment
            assert neutral_article.sentiment_score == 0.0  # Neutral sentiment


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"])) 