# Football News Crawlers

This directory contains web crawlers for gathering football news from various sources, with a focus on Premier League teams and players.

## Directory Structure

```
crawlers/
├── __init__.py           # Crawler registry
├── base_crawler.py       # Base crawler class with common functionality
├── bbc_crawler.py        # BBC Sport crawler implementation
├── ffs_crawler.py        # Fantasy Football Scout crawler
├── goal_crawler.py       # Goal.com crawler (Playwright-based)
├── goal_crawler_requests.py # Goal.com crawler (requests-based)
├── registry.py           # Central crawler registry
├── template_crawler.py   # Template for creating new crawlers
├── test_crawler.py       # Testing utility for crawlers
└── test_bbc_crawler.py   # Example test for BBC crawler
```

## Running the Crawlers

There are two main ways to run the crawlers: testing mode for development and debugging, and production mode for collecting and storing articles in the database.

### Quick Reference

```bash
# 🧪 TESTING (no database required)
python src/crawlers/test_crawler.py bbc                    # Test BBC crawler (all teams)
python src/crawlers/test_crawler.py bbc --team arsenal     # Test BBC crawler for Arsenal
python src/crawlers/test_crawler.py bbc --list-teams       # List available teams
python src/crawlers/test_crawler.py goal --no-headless    # Debug Goal crawler
python src/crawlers/test_crawler.py ffs --limit 10        # Test with limit

# 🐳 DOCKER TESTING (no database required)
docker exec football-news-db-scraper-1 python src/crawlers/test_crawler.py bbc
docker exec football-news-db-scraper-1 python src/crawlers/test_crawler.py bbc --team arsenal
docker exec football-news-db-scraper-1 python src/crawlers/test_crawler.py goal --no-headless
docker exec football-news-db-scraper-1 python src/crawlers/test_crawler.py ffs --limit 10


# 🚀 PRODUCTION (requires database setup)
python run_crawler.py bbc                                 # Run BBC crawler (all teams)
python run_crawler.py bbc --team manchester-city          # Run BBC for Man City only
python run_crawler.py bbc --team arsenal --max-pages 5    # Run BBC for Arsenal, 5 pages
python run_crawler.py bbc --list-teams                    # List available teams
python run_crawler.py goal --limit 20                     # Run Goal crawler with limit
python run_crawler.py ffs                                 # Run Fantasy Football Scout

# 🐳 DOCKER PRODUCTION (recommended for production)
docker exec football-news-db-scraper-1 python run_crawler.py bbc
docker exec football-news-db-scraper-1 python run_crawler.py bbc --team liverpool
docker exec football-news-db-scraper-1 python run_crawler.py ffs --limit 20
docker exec football-news-db-scraper-1 python run_crawler.py goal

# 📊 DATABASE CHECKS (after production runs)
cd scripts/sql_util && ./run_sql.sh articles_today.sql    # Check today's articles
cd scripts/sql_util && ./run_sql.sh load_volumes_by_day.sql # Check volumes
```

### Available Crawlers

The following crawlers are currently available:

- **`bbc`** - BBC Sport football section
- **`ffs`** - Fantasy Football Scout
- **`goal`** - Goal.com (Playwright-based with browser automation)
- **`goal_requests`** - Goal.com (lightweight requests-based)

### Testing Mode (Development & Debugging)

Use the `test_crawler.py` script for development, debugging, and quick testing without database storage.

#### Basic Usage

```bash
# Test a specific crawler
python src/crawlers/test_crawler.py bbc

# Test with custom limit
python src/crawlers/test_crawler.py ffs --limit 10

# Test with verbose output (shows article content)
python src/crawlers/test_crawler.py goal --verbose

# Test Goal crawler with visible browser (for debugging)
python src/crawlers/test_crawler.py goal --no-headless

# Test Goal crawler in headless mode
python src/crawlers/test_crawler.py goal --headless
```

#### Test Script Options

- `crawler` - Name of the crawler to test (`bbc`, `ffs`, `goal`, `goal_requests`)
- `--limit N` - Maximum number of articles to display (default: 5)
- `--verbose` - Display full article content (truncated to 500 characters)
- `--headless` - Force headless mode for browser-based crawlers
- `--no-headless` - Force visible browser mode (useful for debugging)

#### Example Test Output

```
Testing BBC crawler...
Found 15 articles:

Title: Manchester City win Premier League title
URL: https://www.bbc.co.uk/sport/football/article/12345
Published: 2023-05-20T18:30:00+00:00
Teams mentioned: Manchester City
Players mentioned: Erling Haaland, Kevin De Bruyne
--------------------------------------------------------------------------------

Title: Liverpool sign new midfielder
URL: https://www.bbc.co.uk/sport/football/article/12346
Published: 2023-05-19T14:15:00+00:00
Teams mentioned: Liverpool
Players mentioned: 
--------------------------------------------------------------------------------

... and 13 more articles (use --limit to see more)
```

### Production Mode (Database Storage)

Use the `run_crawler.py` script (located in the project root) for production crawling with database storage.

### Docker Production Mode (Recommended)

For production environments, running crawlers in Docker containers is recommended for consistency and isolation.

#### Prerequisites

1. **Database Setup**: Ensure PostgreSQL is running and the database is properly configured
2. **Environment Variables**: Set up your database connection in `src/config/db_config.py`
3. **Dependencies**: Install all required packages including database drivers

#### Basic Usage

```bash
# Run a crawler and save articles to database
python run_crawler.py bbc

# Run with article limit
python run_crawler.py ffs --limit 20

# Run Goal crawler (automatically uses headless mode in production)
python run_crawler.py goal

# Run Goal requests crawler (lightweight, no browser)
python run_crawler.py goal_requests
```

#### Production Script Features

- **Database Integration**: Automatically saves articles to PostgreSQL
- **Duplicate Detection**: Prevents saving duplicate articles
- **Entity Extraction**: Identifies Premier League teams and players mentioned
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Error Handling**: Graceful handling of network and parsing errors

#### Example Production Output

```bash
$ python run_crawler.py bbc --limit 10

INFO - Running bbc crawler...
INFO - Found Premier League article: Arsenal's title hopes dented by shock defeat
INFO - Found Premier League article: Chelsea complete signing of striker
INFO - Collected 8 articles
INFO - Saving 8 articles to database...
INFO - Successfully saved 8 articles to database
INFO - Process completed. 8 articles processed.
```

#### Docker Prerequisites

1. **Docker Compose Running**: Ensure your Docker containers are running
   ```bash
   docker-compose up -d
   ```

2. **Verify Container**: Check that the scraper container is running
   ```bash
   docker ps | grep football-news-db-scraper-1
   ```

#### Docker Usage

```bash
# Basic crawler execution
docker exec football-news-db-scraper-1 python run_crawler.py bbc

# Run with limits
docker exec football-news-db-scraper-1 python run_crawler.py ffs --limit 15

# Run Goal crawler (automatically uses headless mode in Docker)
docker exec football-news-db-scraper-1 python run_crawler.py goal

# Run with interactive output (see logs in real-time)
docker exec -it football-news-db-scraper-1 python run_crawler.py bbc --limit 10
```

#### Docker Advantages

- **Consistent Environment**: Same environment across development and production
- **Database Integration**: Automatic connection to PostgreSQL container
- **Headless Mode**: Goal crawler automatically runs in headless mode
- **Resource Isolation**: Crawlers run in isolated environment
- **Easy Scaling**: Can run multiple container instances if needed

#### Docker Monitoring

```bash
# View crawler logs
docker logs football-news-db-scraper-1

# Follow logs in real-time
docker logs -f football-news-db-scraper-1

# Execute database checks from container
docker exec football-news-db-scraper-1 bash -c "cd scripts/sql_util && ./run_sql.sh articles_today.sql"

# Check container resource usage
docker stats football-news-db-scraper-1
```

#### Example Docker Output

```bash
$ docker exec football-news-db-scraper-1 python run_crawler.py bbc --limit 5

INFO - Running bbc crawler...
INFO - Connected to database: postgresql://postgres:***@db:5432/football-db
INFO - Found Premier League article: Manchester United's transfer update
INFO - Found Premier League article: Liverpool prepare for crucial match
INFO - Collected 5 articles
INFO - Saving 5 articles to database...
INFO - Successfully saved 5 articles to database
INFO - Process completed. 5 articles processed.
```

### Crawler-Specific Notes

#### BBC Crawler (`bbc`)
- **Stability**: Very reliable, rarely blocked
- **Content Quality**: High-quality articles with good metadata
- **Rate Limiting**: Conservative approach, good for production
- **Special Features**: 
  - Automatic user-agent rotation
  - **Team-specific crawling** with pagination support
  - **Embedded article extraction** from team pages
  - **Article link following** for full content
- **Team Crawling**: Supports crawling specific Premier League team pages
- **Pagination**: Automatically handles paginated team content (format: `?page=2`)
- **Content Types**: Extracts both embedded articles and linked articles from team pages

#### Fantasy Football Scout (`ffs`)
- **Content Focus**: Fantasy Premier League focused content
- **Update Frequency**: Multiple daily updates during season
- **Special Features**: FPL-specific player analysis and tips

#### Goal Crawler - Playwright (`goal`)
- **Technology**: Uses Playwright browser automation
- **Performance**: Slower but handles JavaScript-heavy content
- **Browser Modes**: 
  - Headless mode (default in production/containers)
  - Visible browser mode (useful for debugging)
- **Resource Usage**: Higher memory and CPU usage
- **Best For**: When requests-based approach fails

#### Goal Crawler - Requests (`goal_requests`)
- **Technology**: Uses HTTP requests with BeautifulSoup
- **Performance**: Fast and lightweight
- **Limitations**: May miss JavaScript-rendered content
- **Best For**: Production environments where speed matters

### Monitoring and Debugging

#### Checking Database Storage

After running production crawlers, you can verify the data was saved:

```bash
# Check recent articles
cd scripts/sql_util
./run_sql.sh articles_today.sql

# Check load volumes by day
./run_sql.sh load_volumes_by_day.sql
```

#### Common Issues and Solutions

1. **Goal Crawler Browser Issues**:
   ```bash
   # Force headless mode
   python src/crawlers/test_crawler.py goal --headless
   
   # Debug with visible browser
   python src/crawlers/test_crawler.py goal --no-headless
   ```

2. **Database Connection Issues**:
   - Verify PostgreSQL is running
   - Check `DATABASE_URL` in `src/config/db_config.py`
   - Ensure database user has proper permissions

3. **Rate Limiting**:
   - BBC and FFS crawlers include built-in delays
   - Goal crawler uses browser automation with natural timing
   - Avoid running multiple instances simultaneously

4. **Windows PowerShell Path Issues**:
   ```powershell
   # If you get "python: command not found"
   python.exe run_crawler.py bbc
   
   # Or use full paths
   C:\Python\python.exe run_crawler.py bbc
   
   # For testing scripts
   python.exe src/crawlers/test_crawler.py bbc
   ```

5. **Docker Container Issues**:
   ```bash
   # Container not found or not running
   docker-compose up -d
   
   # Container exists but exec fails
   docker restart football-news-db-scraper-1
   
   # Check container logs for errors
   docker logs football-news-db-scraper-1
   
   # Access container shell for debugging
   docker exec -it football-news-db-scraper-1 bash
   
   # Database connection issues in Docker
   docker exec football-news-db-scraper-1 python -c "from src.config.db_config import DATABASE_URL; print(DATABASE_URL)"
   ```

#### Log Analysis

Production crawlers generate detailed logs:

```bash
# Monitor real-time crawling (Linux/Mac)
python run_crawler.py bbc 2>&1 | tee crawler.log

# Windows PowerShell
python run_crawler.py bbc 2>&1 | Tee-Object crawler.log
```

### Performance Tips

- **Best for Speed**: `goal_requests` > `bbc` > `ffs` > `goal`
- **Best for Reliability**: `bbc` > `ffs` > `goal_requests` > `goal`
- **Resource Usage**: `goal` (high) > `ffs` (medium) > `bbc` (low) > `goal_requests` (low)
- **Recommended for Production**: `bbc` (most stable), `ffs` (for FPL content)
- **For JavaScript-heavy sites**: Use `goal` over `goal_requests`
- **Docker vs Local**: Docker adds ~10-15% overhead but provides better isolation and consistency
- **Docker Goal Crawler**: Automatically uses headless mode, saving ~30% memory vs local visible browser

### BBC Team-Specific Crawling

The BBC crawler now supports targeted crawling of specific Premier League team pages with advanced features:

#### Available Teams
```bash
# List all available teams
python run_crawler.py bbc --list-teams

# Available teams include:
# arsenal, manchester-city, liverpool, chelsea, tottenham-hotspur,
# manchester-united, newcastle-united, aston-villa, west-ham-united,
# brighton-and-hove-albion, wolverhampton-wanderers, crystal-palace,
# fulham, brentford, nottingham-forest, everton, afc-bournemouth,
# burnley, leeds-united, sunderland
```

#### Team Page Structure
- **Base URL**: `https://www.bbc.co.uk/sport/football/teams/{team-slug}`
- **Pagination**: `https://www.bbc.co.uk/sport/football/teams/{team-slug}?page=2`
- **Content Types**:
  - **Embedded Articles**: Full articles displayed directly on team pages
  - **Article Links**: Links to separate article pages (`/sport/football/articles/`)

#### Usage Examples
```bash
# Test specific team (development)
python src/crawlers/test_crawler.py bbc --team arsenal --max-pages 2

# Production crawling for specific team
python run_crawler.py bbc --team manchester-city --max-pages 5

# Docker production for specific team
docker exec football-news-db-scraper-1 python run_crawler.py bbc --team liverpool --max-pages 3
```

#### Extracted Data
- **Embedded Articles**: Title, content, author, timestamp, team context
- **Linked Articles**: Full article content from BBC Sport article pages
- **Metadata**: Source team, article type (embedded/linked), publication date
- **Entity Extraction**: Automatic detection of mentioned players and teams

### Development Workflow

1. **Test First**: Always test with `test_crawler.py` before production
2. **Small Batches**: Use `--limit` for initial testing
3. **Debug Mode**: Use `--no-headless` for Goal crawler debugging
4. **Monitor Results**: Check database after production runs
5. **Log Review**: Analyze logs for errors or warnings

### Advanced Testing

For comprehensive testing including Docker integration and database testing, see [TESTING_README.md](TESTING_README.md). This includes:

- **Docker-based Testing**: Full environment testing with database integration
- **Pipeline Testing**: End-to-end testing from crawling to database storage
- **Entity Extraction Testing**: Validation of team and player detection
- **Database Integration**: Testing with real PostgreSQL database

Example Docker testing commands:
```bash
# Full setup and test
./test_crawler_docker.sh full

# Test specific crawler with database
./test_crawler_docker.sh pipeline bbc 10

# Check database contents
./test_crawler_docker.sh check
```

## Creating a New Crawler

### Using the Template Crawler

The `template_crawler.py` file provides a starting point for creating crawlers for new sources. Here's how to create a new crawler:

1. **Copy the template file**:
   ```bash
   cp template_crawler.py your_source_crawler.py
   ```

2. **Update the class name and docstring**:
   ```python
   class YourSourceCrawler(BaseCrawler):
       """
       Crawler for YourSource football news.
       Extracts articles related to Premier League teams and players.
       """
   ```

3. **Implement the required methods**:
   - `crawl()`: Main method to crawl the source for Premier League articles
   - `extract_article_data(url)`: Extract data from a single article
   - `is_premier_league_content(text)`: Determine if content is Premier League related

4. **Add your crawler to the registry**:
   Edit `registry.py` to include your new crawler:
   ```python
   from .your_source_crawler import YourSourceCrawler
   
   # Add to the CRAWLERS dictionary in registry.py
   CRAWLERS = {
       # ... existing crawlers ...
       'your_source': YourSourceCrawler,
   }
   ```

### Example Implementation

Here's a simplified example of how to implement a new crawler:

```python
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import logging
from src.data.premier_league_data import (
    PREMIER_LEAGUE_TEAMS,
    PREMIER_LEAGUE_PLAYERS
)
from src.crawlers.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

class ExampleCrawler(BaseCrawler):
    """
    Crawler for Example.com football news.
    Extracts articles related to Premier League teams and players.
    """
    
    BASE_URL = "https://example.com/football"
    
    def __init__(self):
        super().__init__()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def extract_article_data(self, url: str) -> Optional[Dict]:
        """Extract article data from an Example.com article page."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('h1')
            if not title:
                return None
            title = title.text.strip()
            
            # Extract content
            article_body = soup.find('article')
            if not article_body:
                return None
                
            content = ' '.join([p.text.strip() for p in article_body.find_all('p')])
            
            # Extract publication date
            date_element = soup.find('time')
            published_date = None
            if date_element and date_element.get('datetime'):
                published_date = datetime.fromisoformat(date_element['datetime'].replace('Z', '+00:00'))
            
            # Extract teams and players mentioned in the article
            full_text = f"{title} {content}"
            entities = self.extract_mentioned_entities(full_text)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'published_date': published_date,
                'source': 'Example.com',
                'mentioned_teams': entities['teams'],
                'mentioned_players': entities['players']
            }
            
        except Exception as e:
            logger.error(f"Error extracting article data from {url}: {str(e)}")
            return None

    def crawl(self) -> List[Dict]:
        """Crawl Example.com football section for Premier League articles."""
        articles = []
        try:
            response = self.session.get(self.BASE_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all article links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Check if it's an article link
                if 'article' in href:
                    full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                    
                    # Get the link text and surrounding content to check if it's Premier League related
                    link_text = link.get_text().strip()
                    parent_text = link.parent.get_text().strip()
                    
                    if self.is_premier_league_content(link_text) or self.is_premier_league_content(parent_text):
                        article_data = self.extract_article_data(full_url)
                        if article_data:
                            articles.append(article_data)
                            logger.info(f"Successfully crawled article: {article_data['title']}")
            
        except Exception as e:
            logger.error(f"Error crawling Example.com: {str(e)}")
        
        return articles
```