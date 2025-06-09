#!/bin/bash

# Updated Test Crawler in Docker - Database-Driven Version
# This script tests the crawler functionality with database integration

echo "🚀 Testing Football News Crawler in Docker (Database-Driven)"
echo "==========================================================="

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker first."
        exit 1
    fi
    echo "✅ Docker is running"
}

# Function to check if required files exist
check_files() {
    local required_files=(
        "docker-compose.yml"
        "Dockerfile.scraper"
        "run_crawler.py"
        "src/crawlers/bbc_crawler.py"
        "src/crawlers/ffs_crawler.py"
        "src/data/premier_league_data.py"
        "src/config/db_config.py"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            echo "❌ Missing required file: $file"
            exit 1
        fi
    done
    echo "✅ All required files found"
}

# Function to create .env file if it doesn't exist
setup_env() {
    if [[ ! -f ".env" ]]; then
        echo "📝 Creating .env file from template..."
        cp envexample .env
        echo "⚠️  Please edit .env file with your actual database credentials"
        echo "   Particularly important: POSTGRES_PASSWORD"
    else
        echo "✅ .env file exists"
    fi
}

# Function to build the scraper container
build_scraper() {
    echo "🔨 Building scraper container..."
    docker build -f Dockerfile.scraper -t football-news-scraper .
    if [[ $? -eq 0 ]]; then
        echo "✅ Scraper container built successfully"
    else
        echo "❌ Failed to build scraper container"
        exit 1
    fi
}

# Function to start database
start_database() {
    echo "🗄️  Starting database..."
    docker-compose up -d db
    
    # Wait for database to be ready
    echo "⏳ Waiting for database to be ready..."
    sleep 15
    
    # Check if database is accessible
    docker-compose exec -T db pg_isready -U ${POSTGRES_USER:-postgres}
    if [[ $? -eq 0 ]]; then
        echo "✅ Database is ready"
    else
        echo "❌ Database not ready, waiting longer..."
        sleep 20
        docker-compose exec -T db pg_isready -U ${POSTGRES_USER:-postgres}
        if [[ $? -ne 0 ]]; then
            echo "❌ Database failed to start properly"
            exit 1
        fi
    fi
}

# Function to initialize database schema
init_database() {
    echo "🔄 Initializing database schema..."
    
    docker run --rm \
        --network football-news-db_app-network \
        --env-file .env \
        -e POSTGRES_HOST=db \
        football-news-scraper \
        python -c "
import asyncio
import sys
sys.path.append('/app')
from src.db.database import Database
from src.config.db_config import DATABASE_URL
from sqlalchemy import text

async def init_db():
    try:
        # Connect to database with asyncpg
        await Database.connect_db(DATABASE_URL)
        
        # Drop all tables first to handle schema changes
        print('🗑️  Dropping existing tables...')
        await Database.drop_all_tables()
        
        # Initialize schema
        await Database.init_db()
        
        # Test connection
        async with Database.get_session() as session:
            # Simple query to verify connection
            result = await session.execute(text('SELECT 1'))
            if result.scalar() != 1:
                raise Exception('Database connection test failed')
        
        print('✅ Database schema initialized successfully')
    except Exception as e:
        print(f'❌ Database initialization failed: {e}')
        sys.exit(1)
    finally:
        await Database.close_db()

asyncio.run(init_db())
"
}

# Function to test database connection and data
test_database_data() {
    echo "🔍 Testing database data..."
    
    docker run --rm \
        --network football-news-db_app-network \
        --env-file .env \
        -e POSTGRES_HOST=db \
        football-news-scraper \
        python -c "
import asyncio
import sys
sys.path.append('/app')
from src.db.database import Database
from src.data.premier_league_data import get_data_instance, refresh_all_data
from src.config.db_config import DATABASE_URL
from sqlalchemy import text

async def test_data():
    try:
        # Connect to database with asyncpg
        await Database.connect_db(DATABASE_URL)
        
        # Test connection first
        async with Database.get_session() as session:
            result = await session.execute(text('SELECT 1'))
            if result.scalar() != 1:
                raise Exception('Database connection test failed')
            
            # Refresh data using the same session
            await refresh_all_data(session)
            
            # Get data instance using the same session
            data = await get_data_instance(session)
            
            # Test data access
            teams = data.get_premier_league_teams()
            players = data.get_premier_league_players()
            
            print(f'Found {len(teams)} teams and {len(players)} players')
            
            if not teams or not players:
                print('❌ No data found in database')
                sys.exit(1)
                
            print('✅ Database data test passed')
        
    except Exception as e:
        print(f'❌ Database data test failed: {e}')
        sys.exit(1)
    finally:
        await Database.close_db()

asyncio.run(test_data())
"
}

# Function to test individual crawler with database
test_crawler_with_db() {
    local crawler_name=$1
    local crawler_class
    
    # Convert crawler name to proper class name
    case $crawler_name in
        bbc)
            crawler_class="BBCCrawler"
            ;;
        ffs)
            crawler_class="FFSCrawler"
            ;;
        *)
            echo "Unknown crawler: $crawler_name"
            return 1
            ;;
    esac
    
    echo "🕷️  Testing $crawler_name crawler with database..."
    
    # Run the crawler test with database connection
    docker-compose exec -T scraper python3 -c "
import asyncio
import os
from src.crawlers import $crawler_class
from src.db.database import Database
from src.db.services.article_service import ArticleService
from src.config.db_config import DATABASE_URL
from sqlalchemy.ext.asyncio import AsyncSession

async def main():
    # Initialize database connection using environment variables
    await Database.connect_db(DATABASE_URL)
    
    # Create database session
    async with AsyncSession(Database.engine) as session:
        # Create article service
        article_service = ArticleService(session)
        
        # Create crawler instance
        crawler = $crawler_class(article_service, session)
        
        # Initialize Premier League data
        await crawler.initialize_data(session)
        
        # Run crawler
        articles = await crawler.fetch_articles()
        
        # Print results
        print(f'\nFound {len(articles)} Premier League articles:')
        for article in articles:
            print(f'\nTitle: {article[\"title\"]}')
            print(f'URL: {article[\"url\"]}')
            if article.get('teams'):
                print(f'Teams mentioned: {\", \".join(article[\"teams\"])}')
            if article.get('players'):
                print(f'Players mentioned: {\", \".join(article[\"players\"])}')
            print('-' * 80)
        
        # Close database connection
        await Database.close_db()

if __name__ == '__main__':
    asyncio.run(main())
"
}

# Function to test full pipeline
test_full_pipeline() {
    local crawler_name=$1
    local limit=${2:-5}
    
    echo "🔄 Testing full pipeline: $crawler_name crawler -> database"
    
    docker-compose run --rm scraper python run_crawler.py $crawler_name --limit $limit
}

# Function to check database contents
check_database() {
    echo "🔍 Checking database contents..."
    
    # Source environment variables
    if [[ -f ".env" ]]; then
        set -a
        source .env
        set +a
    fi
    
    docker-compose exec -T db psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-football_news}" -c "
        SELECT 
            'articles' as table_name, 
            COUNT(*) as count 
        FROM article
        UNION ALL
        SELECT 
            'teams' as table_name, 
            COUNT(*) as count 
        FROM team
        UNION ALL
        SELECT 
            'players' as table_name, 
            COUNT(*) as count 
        FROM player;
    "
}

# Function to show recent articles with relationships
show_recent_articles() {
    echo "📰 Recent articles with relationships:"
    
    # Source environment variables
    if [[ -f ".env" ]]; then
        set -a
        source .env
        set +a
    fi
    
    docker-compose exec -T db psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-football_news}" -c "
        SELECT 
            a.title,
            a.source,
            a.published_date,
            COUNT(DISTINCT at.team_id) as team_count,
            COUNT(DISTINCT ap.player_id) as player_count
        FROM article a
        LEFT JOIN article_team at ON a.id = at.article_id
        LEFT JOIN article_player ap ON a.id = ap.article_id
        GROUP BY a.id, a.title, a.source, a.published_date
        ORDER BY a.published_date DESC 
        LIMIT 5;
    "
}

# Function to cleanup
cleanup() {
    echo "🧹 Cleaning up..."
    docker-compose down
    docker image rm football-news-scraper 2>/dev/null || true
}

# Function to run the update_premier_league_data.py script
update_premier_league_data() {
    echo "⚽ Updating Premier League teams and players in the database..."
    docker-compose run --rm scraper python src/scripts/update_premier_league_data.py
}

# Main execution
main() {
    local command=${1:-"full"}
    
    case $command in
        "setup")
            check_docker
            check_files
            setup_env
            build_scraper
            start_database
            init_database
            test_database_data
            echo "✅ Setup complete! Run './test_crawler_docker.sh test' to test crawlers"
            ;;
        "test")
            echo "🧪 Testing crawlers with database..."
            test_crawler_with_db "bbc"
            echo ""
            test_crawler_with_db "ffs"
            ;;
        "pipeline")
            local crawler=${2:-"bbc"}
            local limit=${3:-5}
            echo "🔄 Testing full pipeline with $crawler crawler (limit: $limit)"
            test_full_pipeline $crawler $limit
            check_database
            show_recent_articles
            ;;
        "check")
            check_database
            show_recent_articles
            ;;
        "data")
            test_database_data
            ;;
        "cleanup")
            cleanup
            ;;
        "update-data")
            update_premier_league_data
            ;;
        "full")
            echo "🚀 Running full test sequence..."
            check_docker
            check_files
            setup_env
            build_scraper
            start_database
            init_database
            test_database_data
            echo ""
            echo "Testing crawlers with database..."
            test_crawler_with_db "bbc"
            echo ""
            echo "Testing full pipeline..."
            test_full_pipeline "bbc" 3
            check_database
            show_recent_articles
            ;;
        *)
            echo "Usage: $0 [setup|test|pipeline|check|data|cleanup|full]"
            echo ""
            echo "Commands:"
            echo "  setup     - Build containers, setup database, and initialize schema"
            echo "  test      - Test crawlers with database integration"
            echo "  pipeline  - Test full crawler pipeline with database"
            echo "  check     - Check current database contents"
            echo "  data      - Test database data loading"
            echo "  cleanup   - Stop containers and cleanup"
            echo "  update-data - Update Premier League teams and players in the database"
            echo "  full      - Run complete test sequence (default)"
            echo ""
            echo "Examples:"
            echo "  $0 setup                    # Initial setup with database"
            echo "  $0 test                     # Test crawlers with database"
            echo "  $0 pipeline bbc 10          # Test BBC crawler with 10 articles"
            echo "  $0 check                    # Check database contents"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"