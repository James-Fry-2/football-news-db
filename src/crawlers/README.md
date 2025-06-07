# Football News Crawlers

This directory contains web crawlers for gathering football news from various sources, with a focus on Premier League teams and players.

## Directory Structure

```
crawlers/
├── __init__.py           # Crawler registry
├── base_crawler.py       # Base crawler class with common functionality
├── bbc_crawler.py        # BBC Sport crawler implementation
├── template_crawler.py   # Template for creating new crawlers
├── test_crawler.py       # Testing utility for crawlers
└── test_bbc_crawler.py   # Example test for BBC crawler
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
   Edit `__init__.py` to include your new crawler:
   ```python
   from .your_source_crawler import YourSourceCrawler
   
   # Add to the CRAWLERS dictionary in test_crawler.py
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

## Testing Your Crawler

For detailed testing guidelines and best practices, see [TESTING_README.md](TESTING_README.md).

### Using the Test Crawler

1. **Run the test script**:
   ```bash
   python test_crawler.py your_source
   ```
   Replace `your_source` with the name of your crawler as registered in the `CRAWLERS` dictionary.

2. **View the results**:
   The script will:
   - Initialize your crawler
   - Crawl the source for articles
   - Display the results in the console
   - Show a summary of the crawled articles

3. **Additional options**:
   ```bash
   python test_crawler.py your_source --limit 10 --verbose
   ```
   - `--limit`: Maximum number of articles to display (default: 5)
   - `--verbose`: Display full article content

### Example Test Output

```
Testing bbc crawler...
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

## Base Crawler Functionality

The `base_crawler.py` file provides a base class with common functionality that all crawlers inherit:

- Session management with appropriate headers
- Team and player name lists including nicknames
- Methods for checking if content is Premier League related
- Methods for extracting mentioned teams and players from text

## Premier League Data

Crawlers use the Premier League data from `src/data/premier_league_data.py`, which includes:

- `PREMIER_LEAGUE_TEAMS`: List of current Premier League teams
- `PREMIER_LEAGUE_PLAYERS`: List of notable Premier League players
- `TEAM_NICKNAMES`: Dictionary mapping teams to their nicknames
- `PLAYER_NICKNAMES`: Dictionary mapping players to their nicknames

This data can be refreshed using the `refresh_all_data()` function from the same module. 