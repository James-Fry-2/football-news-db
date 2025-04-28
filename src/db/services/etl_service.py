from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
from .article_service import ArticleService
from ..models.article import Article

class ETLService:
    def __init__(self, article_service: ArticleService):
        self.article_service = article_service

    async def process_articles(self, articles: List[Dict]) -> Dict[str, int]:
        """
        Process a batch of articles and load them into the database.
        
        Args:
            articles: List of article dictionaries to process
            
        Returns:
            Dict containing counts of processed, saved, and skipped articles
        """
        stats = {
            "processed": 0,
            "saved": 0,
            "skipped": 0
        }

        for article_data in articles:
            try:
                stats["processed"] += 1
                
                # Check if article already exists
                if await self.article_service.is_duplicate(article_data["url"]):
                    logger.info(f"Skipping duplicate article: {article_data['url']}")
                    stats["skipped"] += 1
                    continue

                # Save the article
                saved_article = await self.article_service.save_article(article_data)
                if saved_article:
                    logger.info(f"Saved article: {saved_article.title}")
                    stats["saved"] += 1
                else:
                    stats["skipped"] += 1

            except Exception as e:
                logger.error(f"Error processing article {article_data.get('url', 'unknown')}: {e}")
                stats["skipped"] += 1

        return stats

    async def bulk_process_articles(self, articles: List[Dict], batch_size: int = 100) -> Dict[str, int]:
        """
        Process articles in batches for better performance with large datasets.
        
        Args:
            articles: List of article dictionaries to process
            batch_size: Number of articles to process in each batch
            
        Returns:
            Dict containing counts of processed, saved, and skipped articles
        """
        total_stats = {
            "processed": 0,
            "saved": 0,
            "skipped": 0
        }

        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            batch_stats = await self.process_articles(batch)
            
            for key in total_stats:
                total_stats[key] += batch_stats[key]

            logger.info(f"Processed batch {i//batch_size + 1}: {batch_stats}")

        return total_stats 