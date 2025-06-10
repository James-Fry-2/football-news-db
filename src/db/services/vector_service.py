from typing import List, Dict, Optional, Tuple
import hashlib
import json
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from loguru import logger
import openai
from pinecone import Pinecone, ServerlessSpec
import re

from ..models.article import Article
from ...config.vector_config import (
    OPENAI_API_KEY, OPENAI_MODEL,
    PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME, PINECONE_NAMESPACE,
    VECTOR_DIMENSIONS, BATCH_SIZE, MAX_RETRIES, validate_ai_config
)

class VectorService:
    """
    Service for handling OpenAI embeddings and Pinecone vector storage.
    
    Features:
    - Generate embeddings using OpenAI API
    - Store vectors in Pinecone with metadata
    - Semantic search capabilities
    - Batch processing with error handling
    - Simple sentiment analysis
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Initialize Pinecone with new API (v3+)
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Get or create index
        self._ensure_index_exists()
        self.index = self.pc.Index(PINECONE_INDEX_NAME)
        
        # Validate AI configuration
        validate_ai_config()
        
    def _ensure_index_exists(self):
        """Ensure the Pinecone index exists, create if necessary."""
        try:
            existing_indexes = self.pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes.indexes]
            
            if PINECONE_INDEX_NAME not in index_names:
                logger.info(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
                self.pc.create_index(
                    name=PINECONE_INDEX_NAME,
                    dimension=VECTOR_DIMENSIONS,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud=PINECONE_ENVIRONMENT.split('-')[0] if PINECONE_ENVIRONMENT else 'aws',
                        region=PINECONE_ENVIRONMENT.split('-')[1] if '-' in PINECONE_ENVIRONMENT else 'us-east-1'
                    )
                )
                logger.info("Pinecone index created successfully")
            else:
                logger.info(f"Pinecone index {PINECONE_INDEX_NAME} already exists")
                
        except Exception as e:
            logger.error(f"Error ensuring Pinecone index exists: {e}")
            # Don't raise here, let it fail later if index is truly missing

    def _generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    #TODO: implement actual sentiment analysis
    def _calculate_simple_sentiment(self, text: str) -> float:
        """
        Calculate a simple sentiment score based on positive/negative word patterns.
        Returns a score between -1.0 (negative) and 1.0 (positive).
        """
        try:
            # Simple positive and negative word lists
            positive_words = [
                'win', 'won', 'victory', 'champion', 'excellent', 'amazing', 'great',
                'good', 'success', 'celebrate', 'triumph', 'outstanding', 'brilliant',
                'fantastic', 'superb', 'perfect', 'best', 'incredible', 'spectacular'
            ]
            
            negative_words = [
                'lose', 'lost', 'defeat', 'failure', 'terrible', 'awful', 'bad',
                'worst', 'disaster', 'disappointing', 'poor', 'injured', 'injury',
                'suspended', 'banned', 'controversy', 'scandal', 'crisis', 'problem'
            ]
            
            # Clean and tokenize text
            text_lower = re.sub(r'[^\w\s]', ' ', text.lower())
            words = text_lower.split()
            
            if not words:
                return 0.0
            
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            total_sentiment_words = positive_count + negative_count
            
            if total_sentiment_words == 0:
                return 0.0
            
            # Calculate normalized sentiment score
            sentiment_score = (positive_count - negative_count) / len(words)
            # Clamp between -1 and 1
            return max(-1.0, min(1.0, sentiment_score * 10))
            
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return 0.0

    async def generate_embedding(self, text: str, retry_count: int = 0) -> List[float]:
        """
        Generate embeddings using OpenAI's API with error handling and retries.
        
        Args:
            text: Text to embed
            retry_count: Current retry attempt
            
        Returns:
            List of floats representing the embedding
            
        Raises:
            Exception: After max retries exceeded
        """
        try:
            # Truncate text if too long (OpenAI has token limits)
            # text-embedding-3-small supports ~8k tokens
            if len(text) > 8000:
                text = text[:8000] + "..."
                logger.warning("Text truncated for embedding generation")
            
            response = await self.openai_client.embeddings.create(
                model=OPENAI_MODEL,
                input=text,
                encoding_format="float"
            )
            
            return response.data[0].embedding
            
        except openai.RateLimitError as e:
            if retry_count < MAX_RETRIES:
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {retry_count + 1}/{MAX_RETRIES})")
                await asyncio.sleep(wait_time)
                return await self.generate_embedding(text, retry_count + 1)
            else:
                logger.error(f"Rate limit exceeded after {MAX_RETRIES} retries")
                raise
                
        except openai.APIError as e:
            if retry_count < MAX_RETRIES:
                wait_time = 2 ** retry_count
                logger.warning(f"OpenAI API error, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
                return await self.generate_embedding(text, retry_count + 1)
            else:
                logger.error(f"OpenAI API error after {MAX_RETRIES} retries: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def store_vector_in_pinecone(self, vector_id: str, embedding: List[float], metadata: Dict) -> bool:
        """
        Store vector in Pinecone with error handling.
        
        Args:
            vector_id: Unique identifier for the vector
            embedding: The vector embedding
            metadata: Associated metadata
            
        Returns:
            bool: Success status
        """
        try:
            self.index.upsert(
                vectors=[(vector_id, embedding, metadata)],
                namespace=PINECONE_NAMESPACE
            )
            return True
            
        except Exception as e:
            logger.error(f"Error storing vector in Pinecone: {e}")
            return False

    async def process_single_article(self, article_id: int) -> Tuple[bool, str]:
        """
        Process a single article for vector embedding.
        
        Args:
            article_id: ID of the article to process
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get article
            query = select(Article).where(Article.id == article_id)
            result = await self.session.execute(query)
            article = result.scalar_one_or_none()
            
            if not article:
                return False, f"Article {article_id} not found"

            # Check if article is already being processed
            if article.embedding_status == 'processing':
                return False, f"Article {article_id} is already being processed"

            # Generate content for embedding
            content_text = f"{article.title}\n\n{article.content}"
            content_hash = self._generate_content_hash(content_text)

            # Check if already processed with same content
            if (article.content_hash == content_hash and 
                article.embedding_status == 'completed' and 
                article.vector_embedding is not None):
                
                return True, f"Article {article_id} already processed with same content"

            # Update status to processing
            article.embedding_status = 'processing'
            await self.session.commit()

            # Generate embedding
            try:
                embedding = await self.generate_embedding(content_text)
            except Exception as e:
                article.embedding_status = 'failed'
                await self.session.commit()
                return False, f"Failed to generate embedding: {str(e)}"

            # Calculate sentiment
            sentiment_score = self._calculate_simple_sentiment(content_text)

            # Prepare metadata for Pinecone
            vector_id = f"article_{article.id}"
            metadata = {
                "title": article.title[:512],  # Pinecone metadata limits
                "source": article.source,
                "published_date": article.published_date.isoformat() if article.published_date else None,
                "url": article.url[:512],  # Truncate long URLs
                "sentiment": sentiment_score,
                "content_hash": content_hash,
                "article_id": article.id
            }
            
            # Store in Pinecone
            pinecone_success = await self.store_vector_in_pinecone(vector_id, embedding, metadata)
            
            if not pinecone_success:
                article.embedding_status = 'failed'
                await self.session.commit()
                return False, "Failed to store vector in Pinecone"

            # Update article in database
            article.vector_embedding = embedding
            article.search_vector_id = vector_id
            article.content_hash = content_hash
            article.sentiment_score = sentiment_score
            article.embedding_status = 'completed'
            article.updated_at = datetime.now(timezone.utc)

            await self.session.commit()
            
            return True, f"Successfully processed article {article_id}: {article.title[:50]}..."

        except Exception as e:
            # Update status to failed
            try:
                article.embedding_status = 'failed'
                await self.session.commit()
            except Exception as commit_error:
                logger.error(f"Failed to update article status to failed: {commit_error}")
            
            return False, f"Error processing article {article_id}: {str(e)}"

    async def get_pending_articles(self, limit: int = BATCH_SIZE) -> List[int]:
        """Get articles pending vector processing."""
        try:
            query = select(Article.id).where(
                and_(
                    Article.embedding_status.in_(['pending', 'failed']),
                    Article.is_deleted == False
                )
            ).limit(limit)
            
            result = await self.session.execute(query)
            return [row[0] for row in result.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting pending articles: {e}")
            return []

    async def process_batch(self, article_ids: List[int]) -> Dict[str, int]:
        """
        Process a batch of articles with improved concurrency.
        
        Args:
            article_ids: List of article IDs to process
            
        Returns:
            Dict with processing statistics
        """
        stats = {"processed": 0, "succeeded": 0, "failed": 0, "messages": []}
        
        # Process articles sequentially to avoid session conflicts
        semaphore = asyncio.Semaphore(1)  # Sequential processing to prevent database session conflicts
        
        async def process_with_semaphore(article_id: int):
            async with semaphore:
                try:
                    success, message = await self.process_single_article(article_id)
                    stats["processed"] += 1
                    
                    if success:
                        stats["succeeded"] += 1
                        logger.info(message)
                    else:
                        stats["failed"] += 1
                        logger.error(message)
                        
                    stats["messages"].append(f"Article {article_id}: {message}")
                except Exception as e:
                    stats["processed"] += 1
                    stats["failed"] += 1
                    error_msg = f"Error processing article {article_id}: {str(e)}"
                    logger.error(error_msg)
                    stats["messages"].append(error_msg)
                
                # Small delay to be nice to APIs
                await asyncio.sleep(0.2)
        
        # Process all articles concurrently (but limited by semaphore)
        tasks = [process_with_semaphore(article_id) for article_id in article_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

        return stats

    async def process_pending_articles(self, batch_size: int = BATCH_SIZE) -> Dict[str, int]:
        """Process all pending articles in batches."""
        pending_ids = await self.get_pending_articles(batch_size)
        
        if not pending_ids:
            logger.info("No pending articles to process")
            return {"processed": 0, "succeeded": 0, "failed": 0, "messages": []}

        logger.info(f"Processing {len(pending_ids)} pending articles")
        return await self.process_batch(pending_ids)

    async def semantic_search(self, 
                            query: str, 
                            top_k: int = 5, 
                            filter_dict: Optional[Dict] = None,
                            include_scores: bool = True) -> List[Dict]:
        """
        Perform semantic search using Pinecone.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            include_scores: Whether to include similarity scores
            
        Returns:
            List of search results with metadata and scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Prepare search parameters
            search_kwargs = {
                "vector": query_embedding,
                "top_k": top_k,
                "namespace": PINECONE_NAMESPACE,
                "include_metadata": True
            }
            
            if filter_dict:
                search_kwargs["filter"] = filter_dict

            # Search in Pinecone
            results = self.index.query(**search_kwargs)
            
            # Format results
            search_results = []
            for match in results.matches:
                result = {
                    "id": match.id,
                    "metadata": match.metadata or {}
                }
                
                if include_scores:
                    result["score"] = match.score
                    
                search_results.append(result)
            
            logger.info(f"Semantic search returned {len(search_results)} results for query: '{query[:50]}...'")
            return search_results

        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            raise

    async def get_processing_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        try:
            from sqlalchemy import func
            
            query = select(
                Article.embedding_status,
                func.count(Article.id).label('count')
            ).where(
                Article.is_deleted == False
            ).group_by(Article.embedding_status)
            
            result = await self.session.execute(query)
            stats = {row.embedding_status or "unknown": row.count for row in result}
            
            return {
                "pending": stats.get("pending", 0),
                "processing": stats.get("processing", 0),
                "completed": stats.get("completed", 0),
                "failed": stats.get("failed", 0),
                "total": sum(stats.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {e}")
            return {"error": str(e)}

    async def reset_processing_status(self) -> int:
        """
        Reset articles stuck in 'processing' status back to 'pending'.
        Useful for recovery after crashes.
        
        Returns:
            Number of articles reset
        """
        try:
            query = update(Article).where(
                Article.embedding_status == 'processing'
            ).values(
                embedding_status='pending',
                updated_at=datetime.now(timezone.utc)
            )
            
            result = await self.session.execute(query)
            await self.session.commit()
            
            reset_count = result.rowcount
            if reset_count > 0:
                logger.info(f"Reset {reset_count} articles from 'processing' to 'pending' status")
                
            return reset_count
            
        except Exception as e:
            logger.error(f"Error resetting processing status: {e}")
            return 0

    async def delete_vector(self, vector_id: str) -> bool:
        """
        Delete a vector from Pinecone.
        
        Args:
            vector_id: ID of vector to delete
            
        Returns:
            bool: Success status
        """
        try:
            self.index.delete(ids=[vector_id], namespace=PINECONE_NAMESPACE)
            logger.info(f"Deleted vector {vector_id} from Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vector {vector_id}: {e}")
            return False