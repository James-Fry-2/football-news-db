"""
Manual tests for VectorService with real APIs.

These tests require actual API keys and should be run manually
when you want to test against real OpenAI and Pinecone services.

Usage:
    python -m tests.test_vector_manual

Make sure to set environment variables:
    - OPENAI_API_KEY
    - PINECONE_API_KEY
    - PINECONE_ENVIRONMENT
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.db.models.article import Article
from src.db.database import Base
from src.db.services.vector_service import VectorService


class ManualVectorTester:
    """Manual tester for VectorService with real APIs."""
    
    def __init__(self):
        self.engine = None
        self.session = None
        self.service = None
    
    async def setup(self):
        """Setup test database and service."""
        print("🔧 Setting up test environment...")
        
        # Check environment variables
        required_vars = ["OPENAI_API_KEY", "PINECONE_API_KEY", "PINECONE_ENVIRONMENT"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {missing_vars}")
            print("Please set these variables before running manual tests.")
            return False
        
        # Create in-memory database
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.session = async_session()
        
        # Create VectorService with real APIs
        try:
            self.service = VectorService(self.session)
            print("✅ VectorService initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize VectorService: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()
        if self.engine:
            await self.engine.dispose()
        print("🧹 Cleanup complete")
    
    async def create_test_articles(self):
        """Create test articles in database."""
        print("\n📝 Creating test articles...")
        
        articles = [
            Article(
                title="Manchester City's Brilliant Victory",
                url="https://test.com/city-win",
                content="""
                Manchester City secured a brilliant 3-1 victory over Arsenal in a thrilling Premier League encounter. 
                Erling Haaland scored twice in the first half with excellent finishing, while Kevin De Bruyne added a third with a spectacular long-range effort. 
                The victory puts City in a strong position for the title race.
                Arsenal pulled one back through Bukayo Saka but it wasn't enough to prevent the defeat.
                """,
                published_date=datetime.now(timezone.utc),
                source="Test BBC Sport",
                embedding_status='pending'
            ),
            Article(
                title="Liverpool's Injury Crisis Deepens",
                url="https://test.com/liverpool-injuries",
                content="""
                Liverpool face a deepening injury crisis with several key players ruled out for the upcoming fixtures.
                Virgil van Dijk is sidelined with a knee problem, while Mohamed Salah has picked up a hamstring injury.
                The situation is concerning for manager Jurgen Klopp as the team prepares for crucial matches.
                The medical team is working around the clock to get players back to fitness.
                """,
                published_date=datetime.now(timezone.utc),
                source="Test Sky Sports",
                embedding_status='pending'
            ),
            Article(
                title="Chelsea Transfer Update",
                url="https://test.com/chelsea-transfer",
                content="""
                Chelsea are making progress in their pursuit of a new midfielder for the summer transfer window.
                The club has identified several targets and is prepared to make significant investments.
                Negotiations are ongoing with multiple clubs as Chelsea look to strengthen their squad.
                The new additions would provide depth and quality to the team's midfield options.
                """,
                published_date=datetime.now(timezone.utc),
                source="Test ESPN",
                embedding_status='pending'
            )
        ]
        
        for article in articles:
            self.session.add(article)
        
        await self.session.commit()
        
        # Refresh to get IDs
        for article in articles:
            await self.session.refresh(article)
        
        print(f"✅ Created {len(articles)} test articles")
        return articles
    
    async def test_embedding_generation(self):
        """Test embedding generation with real OpenAI API."""
        print("\n🤖 Testing embedding generation...")
        
        test_text = "This is a test article about football and the Premier League."
        
        try:
            embedding = await self.service.generate_embedding(test_text)
            print(f"✅ Generated embedding with {len(embedding)} dimensions")
            print(f"📊 First 5 values: {embedding[:5]}")
            return True
        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            return False
    
    async def test_pinecone_operations(self):
        """Test Pinecone vector operations."""
        print("\n🌲 Testing Pinecone operations...")
        
        # Test vector storage
        test_embedding = [0.1] * 1536
        test_metadata = {
            "title": "Test Article",
            "source": "Manual Test",
            "sentiment": 0.5
        }
        
        try:
            # Store vector
            success = await self.service.store_vector_in_pinecone("manual_test_1", test_embedding, test_metadata)
            if success:
                print("✅ Vector stored successfully in Pinecone")
            else:
                print("❌ Failed to store vector in Pinecone")
                return False
            
            # Test vector deletion
            success = await self.service.delete_vector("manual_test_1")
            if success:
                print("✅ Vector deleted successfully from Pinecone")
            else:
                print("❌ Failed to delete vector from Pinecone")
                return False
                
            return True
        except Exception as e:
            print(f"❌ Pinecone operations failed: {e}")
            return False
    
    async def test_article_processing(self, articles):
        """Test processing real articles."""
        print("\n🔄 Testing article processing...")
        
        # Process first article
        article = articles[0]
        
        try:
            success, message = await self.service.process_sinbbgle_article(article.id)
            
            if success:
                print(f"✅ Article processed: {message}")
                
                # Refresh article to see updates
                await self.session.refresh(article)
                
                print(f"📊 Embedding status: {article.embedding_status}")
                print(f"📊 Sentiment score: {article.sentiment_score}")
                print(f"📊 Vector ID: {article.search_vector_id}")
                print(f"📊 Content hash: {article.content_hash[:16]}...")
                
                return True
            else:
                print(f"❌ Article processing failed: {message}")
                return False
                
        except Exception as e:
            print(f"❌ Article processing error: {e}")
            return False
    
    async def test_batch_processing(self, articles):
        """Test batch processing."""
        print("\n📦 Testing batch processing...")
        
        # Get article IDs that are still pending
        pending_ids = [a.id for a in articles if a.embedding_status == 'pending']
        
        if not pending_ids:
            print("⚠️ No pending articles to process")
            return True
        
        try:
            stats = await self.service.process_batch(pending_ids)
            
            print(f"📊 Batch processing results:")
            print(f"   • Processed: {stats['processed']}")
            print(f"   • Succeeded: {stats['succeeded']}")
            print(f"   • Failed: {stats['failed']}")
            
            # Show some messages
            for msg in stats['messages'][:3]:
                print(f"   • {msg}")
            
            return stats['succeeded'] > 0
            
        except Exception as e:
            print(f"❌ Batch processing error: {e}")
            return False
    
    async def test_semantic_search(self):
        """Test semantic search functionality."""
        print("\n🔍 Testing semantic search...")
        
        search_queries = [
            "Manchester City victory",
            "Liverpool injuries",
            "Chelsea transfer news"
        ]
        
        for query in search_queries:
            try:
                results = await self.service.semantic_search(query, top_k=3)
                
                print(f"\n🔍 Search: '{query}'")
                print(f"📊 Found {len(results)} results")
                
                for i, result in enumerate(results[:2], 1):
                    metadata = result.get('metadata', {})
                    score = result.get('score', 0)
                    title = metadata.get('title', 'Unknown')
                    
                    print(f"   {i}. {title} (score: {score:.3f})")
                
            except Exception as e:
                print(f"❌ Search failed for '{query}': {e}")
                return False
        
        return True
    
    async def test_processing_stats(self):
        """Test processing statistics."""
        print("\n📈 Testing processing statistics...")
        
        try:
            stats = await self.service.get_processing_stats()
            
            print("📊 Processing Statistics:")
            for status, count in stats.items():
                print(f"   • {status}: {count}")
                
            return True
            
        except Exception as e:
            print(f"❌ Stats retrieval failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all manual tests."""
        print("🚀 Starting VectorService Manual Tests")
        print("=" * 50)
        
        # Setup
        if not await self.setup():
            return
        
        test_results = []
        articles = None
        
        try:
            # Test embedding generation
            result = await self.test_embedding_generation()
            test_results.append(("Embedding Generation", result))
            
            # Test Pinecone operations
            result = await self.test_pinecone_operations()
            test_results.append(("Pinecone Operations", result))
            
            # Create test articles
            articles = await self.create_test_articles()
            
            # Test single article processing
            result = await self.test_article_processing(articles)
            test_results.append(("Article Processing", result))
            
            # Test batch processing
            result = await self.test_batch_processing(articles)
            test_results.append(("Batch Processing", result))
            
            # Test semantic search
            result = await self.test_semantic_search()
            test_results.append(("Semantic Search", result))
            
            # Test stats
            result = await self.test_processing_stats()
            test_results.append(("Processing Stats", result))
            
        except Exception as e:
            print(f"❌ Test execution error: {e}")
        
        finally:
            await self.cleanup()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📋 Test Summary:")
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! VectorService is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")


async def main():
    """Main function to run manual tests."""
    tester = ManualVectorTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    # Check if running in async context
    try:
        # This will fail if not in an async context
        asyncio.get_running_loop()
        # If we get here, we're already in an async context
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.create_task(main())
    except RuntimeError:
        # Not in async context, run normally
        asyncio.run(main()) 