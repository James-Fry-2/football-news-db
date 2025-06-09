#!/usr/bin/env python3
"""
Script to process articles with vector embeddings and demonstrate semantic search.

Usage:
    python -m src.scripts.process_vectors --help
    python -m src.scripts.process_vectors --process-batch 10
    python -m src.scripts.process_vectors --search "Manchester United transfer news"
    python -m src.scripts.process_vectors --stats
"""

import asyncio
import argparse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..db.database import get_async_session
from ..db.services.vector_service import VectorService


async def process_pending_articles(batch_size: int = 10):
    """Process pending articles in batches."""
    logger.info(f"Processing pending articles in batches of {batch_size}")
    
    async with get_async_session() as session:
        vector_service = VectorService(session)
        
        # Reset any stuck processing status
        reset_count = await vector_service.reset_processing_status()
        if reset_count > 0:
            logger.info(f"Reset {reset_count} articles from 'processing' to 'pending'")
        
        # Process pending articles
        stats = await vector_service.process_pending_articles(batch_size)
        
        logger.info("Processing completed!")
        logger.info(f"Processed: {stats['processed']}")
        logger.info(f"Succeeded: {stats['succeeded']}")
        logger.info(f"Failed: {stats['failed']}")
        
        if stats['messages']:
            logger.info("Sample messages:")
            for msg in stats['messages'][:5]:  # Show first 5 messages
                logger.info(f"  {msg}")


async def perform_semantic_search(query: str, top_k: int = 5, source_filter: Optional[str] = None):
    """Perform semantic search on processed articles."""
    logger.info(f"Performing semantic search for: '{query}'")
    
    async with get_async_session() as session:
        vector_service = VectorService(session)
        
        # Prepare filter if source specified
        filter_dict = None
        if source_filter:
            filter_dict = {"source": source_filter}
            logger.info(f"Filtering by source: {source_filter}")
        
        try:
            results = await vector_service.semantic_search(
                query=query,
                top_k=top_k,
                filter_dict=filter_dict,
                include_scores=True
            )
            
            logger.info(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                metadata = result['metadata']
                logger.info(f"\n{i}. Score: {result['score']:.4f}")
                logger.info(f"   Title: {metadata.get('title', 'N/A')}")
                logger.info(f"   Source: {metadata.get('source', 'N/A')}")
                logger.info(f"   Date: {metadata.get('published_date', 'N/A')}")
                logger.info(f"   Sentiment: {metadata.get('sentiment', 'N/A')}")
                logger.info(f"   URL: {metadata.get('url', 'N/A')}")
                
        except Exception as e:
            logger.error(f"Search failed: {e}")


async def show_processing_stats():
    """Show processing statistics."""
    logger.info("Fetching processing statistics...")
    
    async with get_async_session() as session:
        vector_service = VectorService(session)
        
        stats = await vector_service.get_processing_stats()
        
        if "error" in stats:
            logger.error(f"Error getting stats: {stats['error']}")
            return
        
        logger.info("Processing Statistics:")
        logger.info(f"  Total articles: {stats['total']}")
        logger.info(f"  Pending: {stats['pending']}")
        logger.info(f"  Processing: {stats['processing']}")
        logger.info(f"  Completed: {stats['completed']}")
        logger.info(f"  Failed: {stats['failed']}")
        
        if stats['total'] > 0:
            completion_rate = (stats['completed'] / stats['total']) * 100
            logger.info(f"  Completion rate: {completion_rate:.1f}%")


async def process_single_article(article_id: int):
    """Process a single article by ID."""
    logger.info(f"Processing article ID: {article_id}")
    
    async with get_async_session() as session:
        vector_service = VectorService(session)
        
        success, message = await vector_service.process_single_article(article_id)
        
        if success:
            logger.info(f"✅ {message}")
        else:
            logger.error(f"❌ {message}")


def main():
    parser = argparse.ArgumentParser(description="Process articles with vector embeddings")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--process-batch", type=int, metavar="SIZE",
                      help="Process pending articles in batches of specified size")
    group.add_argument("--process-article", type=int, metavar="ID",
                      help="Process a single article by ID")
    group.add_argument("--search", type=str, metavar="QUERY",
                      help="Perform semantic search with the given query")
    group.add_argument("--stats", action="store_true",
                      help="Show processing statistics")
    
    parser.add_argument("--top-k", type=int, default=5,
                       help="Number of search results to return (default: 5)")
    parser.add_argument("--source", type=str,
                       help="Filter search results by source")
    
    args = parser.parse_args()
    
    if args.process_batch:
        asyncio.run(process_pending_articles(args.process_batch))
    elif args.process_article:
        asyncio.run(process_single_article(args.process_article))
    elif args.search:
        asyncio.run(perform_semantic_search(args.search, args.top_k, args.source))
    elif args.stats:
        asyncio.run(show_processing_stats())


if __name__ == "__main__":
    main() 