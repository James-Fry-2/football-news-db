from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import Database
from src.db.services.vector_service import VectorService
from src.config.db_config import DATABASE_URL
from loguru import logger
import asyncio

@shared_task(bind=True, max_retries=3)
def process_single_article_task(self, article_id: int):
    """Process a single article for vector embedding."""
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_process_article_async(article_id))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Task failed for article {article_id}: {e}")
        # Retry the task
        self.retry(countdown=60, exc=e)

@shared_task
def process_pending_vectors():
    """Periodic task to process pending vectors."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_process_pending_async())
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        return {"error": str(e)}

async def _process_article_async(article_id: int) -> dict:
    """Async helper for processing single article."""
    await Database.connect_db(DATABASE_URL)
    
    try:
        async with Database.get_session() as session:
            vector_service = VectorService(session)
            success = await vector_service.process_single_article(article_id)
            return {"article_id": article_id, "success": success}
    finally:
        await Database.close_db()

async def _process_pending_async() -> dict:
    """Async helper for processing pending articles."""
    await Database.connect_db(DATABASE_URL)
    
    try:
        async with Database.get_session() as session:
            vector_service = VectorService(session)
            stats = await vector_service.process_pending_articles()
            logger.info(f"Batch processing completed: {stats}")
            return stats
    finally:
        await Database.close_db()