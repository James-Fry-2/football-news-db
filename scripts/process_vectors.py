import asyncio
from src.db.database import Database
from src.db.services.vector_service import VectorService
from src.config.db_config import DATABASE_URL

async def main():
    """Process all pending vectors."""
    await Database.connect_db(DATABASE_URL)
    
    try:
        async with Database.get_session() as session:
            vector_service = VectorService(session)
            
            # Get stats
            stats = await vector_service.get_processing_stats()
            print(f"Processing stats: {stats}")
            
            # Process pending
            if stats["pending"] > 0:
                print(f"Processing {stats['pending']} pending articles...")
                result = await vector_service.process_pending_articles()
                print(f"Result: {result}")
            else:
                print("No pending articles to process")
                
    finally:
        await Database.close_db()

if __name__ == "__main__":
    asyncio.run(main())