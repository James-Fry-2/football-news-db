from typing import List, Dict, Optional
import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
import openai
import pinecone
from ..models.article import Article

class VectorService:
    def __init__(self, session: AsyncSession, openai_api_key: str, pinecone_api_key: str, pinecone_environment: str):
        self.session = session
        self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)
        self.index = pinecone.Index("football-news")

    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash of the content for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI's API."""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def store_embedding(self, article: Article) -> bool:
        """Store article embedding in Pinecone and update database."""
        try:
            # Update article status
            article.embedding_status = 'processing'
            await self.session.commit()

            # Generate content hash
            content_hash = self._generate_content_hash(article.content)
            article.content_hash = content_hash

            # Generate embedding
            embedding = await self.generate_embedding(article.content)
            article.vector_embedding = embedding

            # Store in Pinecone
            vector_id = f"article_{article.id}"
            metadata = {
                "title": article.title,
                "source": article.source,
                "published_date": article.published_date.isoformat(),
                "url": article.url
            }
            
            self.index.upsert(
                vectors=[(vector_id, embedding, metadata)],
                namespace="articles"
            )
            
            article.search_vector_id = vector_id
            article.embedding_status = 'completed'
            await self.session.commit()
            
            logger.info(f"Successfully stored embedding for article: {article.title}")
            return True

        except Exception as e:
            article.embedding_status = 'failed'
            await self.session.commit()
            logger.error(f"Error storing embedding for article {article.id}: {e}")
            return False

    async def semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Perform semantic search using Pinecone."""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace="articles",
                include_metadata=True
            )
            
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

    async def process_pending_articles(self, batch_size: int = 10) -> Dict[str, int]:
        """Process articles that are pending embedding generation."""
        stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0
        }

        try:
            # Get pending articles
            query = select(Article).where(
                Article.embedding_status == 'pending'
            ).limit(batch_size)
            
            result = await self.session.execute(query)
            articles = result.scalars().all()

            for article in articles:
                stats["processed"] += 1
                success = await self.store_embedding(article)
                if success:
                    stats["succeeded"] += 1
                else:
                    stats["failed"] += 1

            logger.info(f"Processed {stats['processed']} articles: {stats['succeeded']} succeeded, {stats['failed']} failed")
            return stats

        except Exception as e:
            logger.error(f"Error processing pending articles: {e}")
            raise

    async def delete_embedding(self, article_id: int) -> bool:
        """Delete article embedding from Pinecone."""
        try:
            article = await self.session.get(Article, article_id)
            if not article or not article.search_vector_id:
                return False

            # Delete from Pinecone
            self.index.delete(
                ids=[article.search_vector_id],
                namespace="articles"
            )

            # Clear vector-related fields
            article.vector_embedding = None
            article.embedding_status = 'pending'
            article.search_vector_id = None
            article.sentiment_score = None
            await self.session.commit()

            logger.info(f"Successfully deleted embedding for article {article_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting embedding for article {article_id}: {e}")
            return False 