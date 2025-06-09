#!/usr/bin/env python3
"""
LLM Processor - Continuously process articles with OpenAI embeddings and store in Pinecone.

This script runs in the LLM container and processes pending articles in batches.
"""

import asyncio
import signal
import sys
from loguru import logger
from datetime import datetime

from ..db.database import get_async_session
from ..db.services.vector_service import VectorService


class LLMProcessor:
    def __init__(self, batch_size: int = 10, sleep_interval: int = 30):
        self.batch_size = batch_size
        self.sleep_interval = sleep_interval
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def process_batch(self) -> dict:
        """Process a batch of pending articles."""
        try:
            async with get_async_session() as session:
                vector_service = VectorService(session)
                
                # Reset any stuck processing articles first
                reset_count = await vector_service.reset_processing_status()
                if reset_count > 0:
                    logger.info(f"Reset {reset_count} articles from 'processing' to 'pending'")
                
                # Process pending articles
                stats = await vector_service.process_pending_articles(self.batch_size)
                
                if stats['processed'] > 0:
                    logger.info(f"Batch completed: {stats['succeeded']} succeeded, {stats['failed']} failed")
                    
                    # Log some sample messages
                    for msg in stats.get('messages', [])[:3]:
                        logger.debug(msg)
                else:
                    logger.debug("No pending articles to process")
                
                return stats
                
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            return {"processed": 0, "succeeded": 0, "failed": 1, "error": str(e)}
    
    async def get_stats(self) -> dict:
        """Get current processing statistics."""
        try:
            async with get_async_session() as session:
                vector_service = VectorService(session)
                return await vector_service.get_processing_stats()
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    async def run(self):
        """Main processing loop."""
        logger.info("🚀 LLM Processor starting...")
        logger.info(f"Batch size: {self.batch_size}, Sleep interval: {self.sleep_interval}s")
        
        # Log initial stats
        initial_stats = await self.get_stats()
        if "error" not in initial_stats:
            logger.info(f"Initial stats: {initial_stats['pending']} pending, {initial_stats['completed']} completed")
        
        batch_count = 0
        total_processed = 0
        total_succeeded = 0
        total_failed = 0
        
        while self.running:
            try:
                batch_count += 1
                logger.debug(f"Starting batch #{batch_count}")
                
                # Process a batch
                stats = await self.process_batch()
                
                # Update totals
                total_processed += stats.get('processed', 0)
                total_succeeded += stats.get('succeeded', 0)
                total_failed += stats.get('failed', 0)
                
                # Log progress every 10 batches or when articles are processed
                if batch_count % 10 == 0 or stats.get('processed', 0) > 0:
                    current_stats = await self.get_stats()
                    if "error" not in current_stats:
                        completion_rate = (current_stats['completed'] / max(current_stats['total'], 1)) * 100
                        logger.info(f"Progress: {current_stats['completed']}/{current_stats['total']} articles ({completion_rate:.1f}% complete)")
                        logger.info(f"Session totals: {total_succeeded} succeeded, {total_failed} failed")
                
                # Sleep before next batch
                if self.running:
                    await asyncio.sleep(self.sleep_interval)
                    
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                if self.running:
                    await asyncio.sleep(self.sleep_interval)
        
        logger.info("🏁 LLM Processor stopped")
        logger.info(f"Final session stats: {total_processed} processed, {total_succeeded} succeeded, {total_failed} failed")


async def main():
    """Main entry point."""
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Get configuration from environment
    import os
    batch_size = int(os.getenv("BATCH_SIZE", "10"))
    sleep_interval = int(os.getenv("PROCESSING_INTERVAL", "30"))
    
    logger.info(f"Configuration: batch_size={batch_size}, sleep_interval={sleep_interval}s")
    
    # Start processor
    processor = LLMProcessor(batch_size=batch_size, sleep_interval=sleep_interval)
    await processor.run()


if __name__ == "__main__":
    asyncio.run(main()) 