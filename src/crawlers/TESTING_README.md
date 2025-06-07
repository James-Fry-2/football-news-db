# Testing Football News Crawlers in Docker

This guide explains how to test the football news crawlers using Docker containers with database integration.

## Prerequisites

- Docker and Docker Compose installed
- Project files properly set up (see setup section below)
- At least 2GB available memory for containers

## Quick Start

1. **Initial Setup**:
   ```bash
   # Make the test script executable
   chmod +x test_crawler_docker.sh
   
   # Run complete test sequence
   ./test_crawler_docker.sh full
   ```

2. **Check Results**:
   ```bash
   # View what was crawled and saved
   ./test_crawler_docker.sh check
   ```

## Test Script Commands

### `./test_crawler_docker.sh setup`
Sets up the complete testing environment:
- ✅ Builds Docker containers
- ✅ Starts PostgreSQL database
- ✅ Creates database schema
- ✅ Populates with Premier League teams and players
- ✅ Validates data loading

**Expected Output**:
```
✅ Docker is running
✅ All required files found
✅ Scraper container built successfully
✅ Database is ready
✅ Database schema initialized successfully
✅ Teams populated: 20 teams
✅ Players populated: 50+ created
✅ Loaded 20 teams from database
✅ Loaded 50+ players from database
```

### `./test_crawler_docker.sh test`
Tests crawlers without saving to database:
- 🕷️ Tests BBC crawler with database integration
- 🕷️ Tests Fantasy Football Scout crawler
- 📊 Shows extracted teams and players
- ✅ Validates entity extraction

**Expected Output**:
```
🕷️ Testing bbc crawler with database...
Found 15 Premier League articles:

1. Manchester City secure top spot with victory
   URL: https://www.bbc.co.uk/sport/football/article/123
   Source: BBC Sport
   Teams: ['Manchester City', 'Liverpool']
   Players: ['Erling Haaland', 'Kevin De Bruyne']

2. Arsenal's title hopes boosted by win
   URL: https://www.bbc.co.uk/sport/football/article/124
   Teams: ['Arsenal']
   Players: ['Bukayo Saka', 'Martin Ødegaard']
```

### `./test_crawler_docker.sh pipeline [crawler] [limit]`
Tests full pipeline (crawler → database):
- 🔄 Runs specified crawler
- 💾 Saves articles to database
- 🔗 Creates team/player relationships
- 📈 Shows database statistics

**Examples**:
```bash
# Test BBC crawler with 5 articles
./test_crawler_docker.sh pipeline bbc 5

# Test Fantasy Football Scout with 10 articles
./test_crawler_docker.sh pipeline ffs 10
```

**Expected Output**:
```
🔄 Testing full pipeline with bbc crawler (limit: 5)
Collected 5 articles
Successfully processed 5 articles: 5 succeeded, 0 failed
Upload complete

🔍 Checking database contents...
 table_name | count 
------------+-------
 articles   |     5
 teams      |    20
 players    |    67
```

### `./test_crawler_docker.sh check`
Displays current database contents:
- 📊 Article, team, and player counts
- 📰 Recent articles with relationships
- 🔍 Database statistics

**Expected Output**:
```
🔍 Checking database contents...
 table_name | count 
------------+-------
 articles   |    25
 teams      |    20
 players    |    67

📰 Recent articles with relationships:
                    title                     |  source   |    published_date    | team_count | player_count
----------------------------------------------+-----------+---------------------+------------+--------------
 City close in on Premier League title       | BBC Sport | 2024-06-05 14:30:00 |          2 |            3
 Arsenal prepare for crucial fixture         | BBC Sport | 2024-06-05 13:15:00 |          1 |            2
```

### `./test_crawler_docker.sh data`
Tests database data loading without crawling:
- 🗄️ Validates database connection
- 📋 Tests Premier League data loading
- 🔍 Tests entity extraction functionality

### `./test_crawler_docker.sh cleanup`
Stops containers and removes test data:
- 🛑 Stops all containers
- 🧹 Removes container images
- 🗑️ Cleans up test environment

## Setup Requirements

Before running the tests, ensure these files exist:

### Required Files:
```
project-root/
├── src/
│   ├── data/
│   │   ├── __init__.py
│   │   └── premier_league_data.py     # Database-driven data module
│   ├── config/
│   │   └── db_config.py              # Database configuration
│   ├── crawlers/
│   │   ├── base_crawler.py           # Updated base crawler
│   │   ├── bbc_crawler.py            # BBC crawler implementation
│   │   └── ffs_crawler.py            # Fantasy Football Scout crawler
│   └── db/
│       └── models/                   # Database models
├── scripts/
│   ├── populate_database.py          # Database population script
│   └── validate_setup.py            # Setup validation
├── docker-compose.yml
├── Dockerfile.scraper
├── test_crawler_docker.sh           # Main test script
├── .env                             # Environment variables
└── envexample                       # Environment template
```

### Environment Setup:
1. **Copy environment template**:
   ```bash
   cp envexample .env
   ```

2. **Edit `.env` file** with your settings:
   ```bash
   # Database Configuration
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_secure_password
   POSTGRES_DB=footbal-db
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   ```

## Troubleshooting

### Common Issues and Solutions:

#### ❌ "Docker is not running"
```bash
# Start Docker Desktop or Docker service
sudo systemctl start docker  # Linux
# or restart Docker Desktop (Windows/Mac)
```

#### ❌ "Missing required file: src/data/premier_league_data.py"
```bash
# Create the missing data files using the provided templates
mkdir -p src/data src/config
# Copy the premier_league_data.py and db_config.py files
```

#### ❌ "Database not ready"
```bash
# Check database container status
docker-compose ps

# View database logs
docker-compose logs db

# Restart database if needed
docker-compose restart db
```

#### ❌ "Failed to build scraper container"
```bash
# Check for syntax errors in Dockerfile.scraper
# Rebuild with verbose output
docker build -f Dockerfile.scraper -t football-news-scraper . --no-cache
```

#### ❌ "Import error" during crawler test
```bash
# Validate setup first
python scripts/validate_setup.py

# Check if all Python dependencies are installed
pip install -r requirements/base.txt
```

### Debug Commands:

```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs scraper
docker-compose logs db

# Access database directly
docker-compose exec db psql -U postgres -d football_news

# Inspect container
docker run -it --entrypoint /bin/bash football-news-scraper

# Test database connection
docker-compose exec db pg_isready -U postgres
```

## Testing Workflow

### Development Testing:
```bash
# 1. Initial setup (run once)
./test_crawler_docker.sh setup

# 2. Test individual crawlers during development
./test_crawler_docker.sh test

# 3. Test specific changes
./test_crawler_docker.sh pipeline bbc 3

# 4. Check results
./test_crawler_docker.sh check
```

### Production Validation:
```bash
# 1. Full test with larger dataset
./test_crawler_docker.sh pipeline bbc 50
./test_crawler_docker.sh pipeline ffs 25

# 2. Validate database integrity
./test_crawler_docker.sh check

# 3. Performance testing
time ./test_crawler_docker.sh pipeline bbc 100
```

### Cleanup After Testing:
```bash
# Remove test containers and data
./test_crawler_docker.sh cleanup

# Optional: Remove all Docker data
docker system prune -a
```

## Expected Performance

### Typical Results:
- **Setup Time**: 2-5 minutes (first run)
- **Crawler Speed**: 5-10 articles per minute
- **Database Operations**: Sub-second for most queries
- **Memory Usage**: ~500MB for containers

### Success Indicators:
- ✅ All containers start successfully
- ✅ Database contains 20 teams and 50+ players
- ✅ Crawlers find relevant Premier League articles
- ✅ Entity extraction identifies teams and players correctly
- ✅ Articles are saved with proper relationships

## Advanced Usage

### Custom Testing:
```bash
# Test with environment variables
POSTGRES_PASSWORD=custom_pass ./test_crawler_docker.sh setup

# Test specific crawler limit
./test_crawler_docker.sh pipeline bbc 100

# Run in verbose mode (add to script if needed)
DEBUG=1 ./test_crawler_docker.sh test
```

### Integration with CI/CD:
```bash
# Non-interactive testing
CI=true ./test_crawler_docker.sh full

# Exit codes: 0 = success, 1 = failure
echo $?  # Check exit status
```

### Monitoring:
```bash
# Watch database growth
watch './test_crawler_docker.sh check'

# Monitor container resources
docker stats

# View real-time logs
docker-compose logs -f scraper
```

This testing framework provides a complete validation of your crawler system, ensuring that web scraping, database integration, and entity extraction all work correctly in a containerized environment.