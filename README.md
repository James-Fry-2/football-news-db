# Football News Database

A collection of web crawlers for gathering football news from various sources, with a focus on Premier League teams and players.

## Overview

This project contains crawlers for various football news websites, including:
- BBC Sport
- Sky Sports
- The Guardian
- And more...

Each crawler is designed to extract articles related to Premier League teams and players, storing them in a structured format for further analysis.

## Creating a New Crawler

### Using the Template Crawler

The project includes a template crawler that you can use as a starting point for creating crawlers for new sources. Here's how to create a new crawler:

1. **Copy the template file**:
   ```bash
   cp src/crawlers/template_crawler.py src/crawlers/your_source_crawler.py
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
   - `_get_article_urls()`: Extract article URLs from the source's football section
   - `_extract_article_data(url)`: Extract data from a single article
   - `_is_relevant_article(title, content)`: Determine if an article is relevant

4. **Add your crawler to the registry**:
   Edit `src/crawlers/__init__.py` to include your new crawler:
   ```python
   from .your_source_crawler import YourSourceCrawler
   
   # Add to the CRAWLER_REGISTRY dictionary
   CRAWLER_REGISTRY = {
       # ... existing crawlers ...
       "your_source": YourSourceCrawler,
   }
   ```

### Example Implementation

Here's a simplified example of how to implement a new crawler:

```python
from bs4 import BeautifulSoup
import requests
from typing import List, Dict, Optional
from datetime import datetime
import re

from .base_crawler import BaseCrawler
from ..data.premier_league_data import PREMIER_LEAGUE_TEAMS, PREMIER_LEAGUE_PLAYERS

class ExampleCrawler(BaseCrawler):
    """
    Crawler for Example.com football news.
    Extracts articles related to Premier League teams and players.
    """
    
    def __init__(self):
        super().__init__("Example", "https://example.com/football")
    
    def _get_article_urls(self) -> List[str]:
        """Extract article URLs from the football section."""
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all article links (adjust selectors for your source)
            article_links = soup.select('article a, .news-item a, .story-link')
            
            # Extract and return unique URLs
            urls = [link.get('href') for link in article_links if link.get('href')]
            return list(set(urls))
        except Exception as e:
            self.logger.error(f"Error getting article URLs: {e}")
            return []
    
    def _extract_article_data(self, url: str) -> Optional[Dict]:
        """Extract data from a single article."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title (adjust selector for your source)
            title_elem = soup.select_one('h1, .article-title, .headline')
            title = title_elem.text.strip() if title_elem else ""
            
            # Extract content (adjust selector for your source)
            content_elem = soup.select_one('article, .article-content, .story-body')
            content = content_elem.text.strip() if content_elem else ""
            
            # Extract publication date (adjust selector and parsing for your source)
            date_elem = soup.select_one('.published-date, .article-date, time')
            date_str = date_elem.get('datetime') if date_elem and date_elem.get('datetime') else date_elem.text.strip() if date_elem else ""
            
            # Parse the date (adjust format for your source)
            try:
                pub_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                try:
                    pub_date = datetime.strptime(date_str, "%d %B %Y, %H:%M")
                except ValueError:
                    pub_date = datetime.now()
            
            # Check if the article is relevant
            if not self._is_relevant_article(title, content):
                return None
            
            # Return the extracted data
            return {
                "title": title,
                "content": content,
                "url": url,
                "source": self.source_name,
                "published_date": pub_date.isoformat(),
                "crawled_date": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error extracting article data from {url}: {e}")
            return None
    
    def _is_relevant_article(self, title: str, content: str) -> bool:
        """Determine if an article is relevant to Premier League teams or players."""
        # Combine title and content for searching
        text = f"{title} {content}".lower()
        
        # Check for team names
        for team in PREMIER_LEAGUE_TEAMS:
            if team.lower() in text:
                return True
        
        # Check for player names
        for player in PREMIER_LEAGUE_PLAYERS:
            if player.lower() in text:
                return True
        
        # Check for common Premier League terms
        premier_league_terms = ["premier league", "premier", "epl", "english premier league"]
        for term in premier_league_terms:
            if term in text:
                return True
        
        return False
```

## Testing Your Crawler

The project includes a `test_crawler.py` script that allows you to test your crawler before integrating it into the main system.

### Using the Test Crawler

1. **Run the test script**:
   ```bash
   python src/test_crawler.py your_source
   ```
   Replace `your_source` with the name of your crawler as registered in the `CRAWLER_REGISTRY`.

2. **View the results**:
   The script will:
   - Initialize your crawler
   - Fetch article URLs
   - Extract data from a sample of articles
   - Display the results in the console
   - Save the results to a JSON file in the `data` directory

3. **Analyze the output**:
   - Check the console output for any errors or warnings
   - Review the extracted data for accuracy
   - Verify that the relevance filtering is working correctly

### Example Test Output

```
Testing ExampleCrawler...
Found 25 article URLs
Extracting data from 5 sample articles...
Article 1: "Example Team Wins Match" - Relevant: True
Article 2: "Other Sports News" - Relevant: False
Article 3: "Player Transfer News" - Relevant: True
Article 4: "Weather Forecast" - Relevant: False
Article 5: "Premier League Table" - Relevant: True
Extracted 3 relevant articles
Results saved to data/example_crawler_test_results.json
```

## Refreshing Premier League Data

The project includes functionality to refresh the Premier League teams and players data from external sources.

### Using the Refresh Function

1. **Import the refresh function**:
   ```python
   from src.data.premier_league_data import refresh_all_data
   ```

2. **Call the function**:
   ```python
   teams_updated, players_updated, nicknames_updated = refresh_all_data()
   ```

3. **Check the results**:
   ```python
   if teams_updated:
       print("Teams data updated successfully")
   if players_updated:
       print("Players data updated successfully")
   if nicknames_updated:
       print("Nicknames data updated successfully")
   ```

## Project Structure

```
football-news-db/
├── data/                      # Data storage directory
│   ├── premier_league_teams.json
│   ├── premier_league_players.json
│   └── premier_league_nicknames.json
├── src/
│   ├── crawlers/              # Crawler implementations
│   │   ├── __init__.py        # Crawler registry
│   │   ├── base_crawler.py    # Base crawler class
│   │   ├── bbc_crawler.py     # BBC Sport crawler
│   │   ├── sky_crawler.py     # Sky Sports crawler
│   │   ├── template_crawler.py # Template for new crawlers
│   │   └── ...                # Other crawlers
│   ├── data/                  # Data management
│   │   └── premier_league_data.py
│   └── test_crawler.py        # Testing utility
└── README.md                  # This file
```

## Requirements

- Python 3.8+
- BeautifulSoup4
- Requests
- Other dependencies listed in `requirements.txt`

## License

[Your License Here] 