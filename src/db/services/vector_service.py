from typing import List, Dict, Optional
import hashlib
import json
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from loguru import logger
import openai
import pinecone
from textblob import TextBlob

from ..models.article import Article
from ...config.vector_config import (
    OPENAI_API_KEY, OPENAI_MODEL,
    PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME, PINECONE_NAMESPACE,
    VECTOR_DIMENSIONS, BATCH_SIZE, MAX_RETRIES
)

class VectorService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Initialize Pinecone
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
        self.index = pinecone.Index(PINECONE_INDEX_NAME)
        
    def _generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score using TextBlob."""
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity  # Returns -1 to 1
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return 0.0

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI's API with error handling."""
        try:
            # Truncate text if too long (OpenAI has token limits)
            if len(text) > 8000:  # Conservative limit
                text = text[:8000] + "..."
            
            response = await self.openai_client.embeddings.create(
                model=OPENAI_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def process_single_article(self, article_id: int) -> bool:
        """Process a single article for vector embedding."""
        try:
            # Get article
            query = select(Article).where(Article.id == article_id)
            result = await self.session.execute(query)
            article = result.scalar_one_or_none()
            
            if not article:
                logger.warning(f"Article {article_id} not found")
                return False

            # Update status to processing
            article.embedding_status = 'processing'
            await self.session.commit()

            # Generate content hash
            content_text = f"{article.title}\n\n{article.content}"
            content_hash = self._generate_content_hash(content_text)

            # Check if already processed (same content hash)
            if article.content_hash == content_hash and article.embedding_status == 'completed':
                logger.info(f"Article {article_id} already processed with same content")
                return True

            # Generate embedding
            embedding = await self.generate_embedding(content_text)

            # Calculate sentiment
            sentiment_score = self._calculate_sentiment(content_text)

            # Store in Pinecone
            vector_id = f"article_{article.id}"
            metadata = {
                "title": article.title,
                "source": article.source,
                "published_date": article.published_date.isoformat() if article.published_date else None,
                "url": article.url,
                "sentiment": sentiment_score
            }
            
            self.index.upsert(
                vectors=[(vector_id, embedding, metadata)],
                namespace=PINECONE_NAMESPACE
            )

            # Update article in database
            article.vector_embedding = embedding
            article.search_vector_id = vector_id
            article.content_hash = content_hash
            article.sentiment_score = sentiment_score
            article.embedding_status = 'completed'
            article.updated_at = datetime.now(timezone.utc)

            await self.session.commit()
            
            logger.info(f"Successfully processed article {article_id}: {article.title}")
            return True

        except Exception as e:
            # Update status to failed
            try:
                article.embedding_status = 'failed'
                await self.session.commit()
            except:
                pass
            
            logger.error(f"Error processing article {article_id}: {e}")
            return False

    async def get_pending_articles(self, limit: int = BATCH_SIZE) -> List[int]:
        """Get articles pending vector processing."""
        query = select(Article.id).where(
            Article.embedding_status.in_(['pending', 'failed'])
        ).limit(limit)
        
        result = await self.session.execute(query)
        return [row[0] for row in result.fetchall()]

    async def process_batch(self, article_ids: List[int]) -> Dict[str, int]:
        """Process a batch of articles."""
        stats = {"processed": 0, "succeeded": 0, "failed": 0}
        
        for article_id in article_ids:
            stats["processed"] += 1
            success = await self.process_single_article(article_id)
            
            if success:
                stats["succeeded"] += 1
            else:
                stats["failed"] += 1
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)

        return stats

    async def process_pending_articles(self, batch_size: int = BATCH_SIZE) -> Dict[str, int]:
        """Process all pending articles in batches."""
        pending_ids = await self.get_pending_articles(batch_size)
        
        if not pending_ids:
            logger.info("No pending articles to process")
            return {"processed": 0, "succeeded": 0, "failed": 0}

        logger.info(f"Processing {len(pending_ids)} pending articles")
        return await self.process_batch(pending_ids)

    async def semantic_search(self, query: str, top_k: int = 5, filter_dict: Dict = None) -> List[Dict]:
        """Perform semantic search using Pinecone."""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Search in Pinecone
            search_kwargs = {
                "vector": query_embedding,
                "top_k": top_k,
                "namespace": PINECONE_NAMESPACE,
                "include_metadata": True
            }
            
            if filter_dict:
                search_kwargs["filter"] = filter_dict

            results = self.index.query(**search_kwargs)
            
            # Format results
            search_results = []
            for match in results.matches:
                search_results.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            return search_results

        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            raise

    async def get_processing_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        from sqlalchemy import func
        
        query = select(
            Article.embedding_status,
            func.count(Article.id).label('count')
        ).group_by(Article.embedding_status)
        
        result = await self.session.execute(query)
        stats = {row.embedding_status: row.count for row in result}
        
        return {
            "pending": stats.get("pending", 0),
            "processing": stats.get("processing", 0),
            "completed": stats.get("completed", 0),
            "failed": stats.get("failed", 0),
            "total": sum(stats.values())
        }