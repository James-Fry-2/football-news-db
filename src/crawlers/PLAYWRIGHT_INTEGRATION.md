# Integrating Playwright with Football News Crawlers

This document provides guidance on how to integrate [Playwright](https://playwright.dev/docs/intro) with the football news crawlers for more advanced web scraping capabilities.

## Why Playwright?

Playwright is a powerful browser automation tool that offers several advantages over traditional web scraping approaches:

- **Modern Browser Support**: Works with Chromium, Firefox, and WebKit
- **JavaScript Rendering**: Can execute JavaScript and handle dynamic content
- **Network Interception**: Can intercept and modify network requests
- **Authentication Handling**: Supports various authentication methods
- **Screenshots and Videos**: Can capture screenshots and record videos
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

To add Playwright to your project:

```bash
# Using pip
pip install playwright
playwright install  # Install browser binaries

# Or using poetry
poetry add playwright
poetry run playwright install
```

## Basic Integration Example

Here's how to modify a crawler to use Playwright:

```python
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import logging

from src.crawlers.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)

class PlaywrightCrawler(BaseCrawler):
    """
    Example crawler using Playwright for advanced web scraping.
    """
    
    BASE_URL = "https://example.com/football"
    
    def __init__(self):
        super().__init__()
        self.playwright = None
        self.browser = None
        self.context = None
    
    def _setup_playwright(self):
        """Initialize Playwright and browser."""
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
    
    def _cleanup_playwright(self):
        """Clean up Playwright resources."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
            self.browser = None
            self.context = None
    
    def extract_article_data(self, url: str) -> Optional[Dict]:
        """Extract article data using Playwright."""
        try:
            self._setup_playwright()
            page = self.context.new_page()
            
            # Navigate to the page and wait for content to load
            page.goto(url, wait_until="networkidle")
            
            # Wait for specific elements if needed
            page.wait_for_selector("h1", timeout=5000)
            
            # Get the page content
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
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
            entities = this.extract_mentioned_entities(full_text)
            
            # Close the page
            page.close()
            
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
        finally:
            # Clean up resources
            self._cleanup_playwright()
    
    def crawl(self) -> List[Dict]:
        """Crawl the source for Premier League articles using Playwright."""
        articles = []
        try:
            self._setup_playwright()
            page = self.context.new_page()
            
            # Navigate to the base URL
            page.goto(this.BASE_URL, wait_until="networkidle")
            
            # Wait for content to load
            page.wait_for_selector("a", timeout=5000)
            
            # Get all links
            links = page.query_selector_all("a")
            
            for link in links:
                href = link.get_attribute("href")
                if not href:
                    continue
                
                # Check if it's an article link
                if 'article' in href:
                    full_url = href if href.startswith('http') else f"{this.BASE_URL}{href}"
                    
                    # Get the link text
                    link_text = link.inner_text()
                    
                    if this.is_premier_league_content(link_text):
                        article_data = this.extract_article_data(full_url)
                        if article_data:
                            articles.append(article_data)
                            logger.info(f"Successfully crawled article: {article_data['title']}")
            
            # Close the page
            page.close()
            
        except Exception as e:
            logger.error(f"Error crawling Example.com: {str(e)}")
        finally:
            # Clean up resources
            this._cleanup_playwright()
        
        return articles
```

## Advanced Features

### Handling Authentication

```python
def _authenticate(self):
    """Authenticate with the website if needed."""
    page = self.context.new_page()
    page.goto("https://example.com/login")
    page.fill("input[name='username']", "your_username")
    page.fill("input[name='password']", "your_password")
    page.click("button[type='submit']")
    page.wait_for_navigation()
    page.close()
```

### Intercepting Network Requests

```python
def _setup_network_interception(self):
    """Set up network request interception."""
    self.context.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())
    self.context.route("**/analytics.js", lambda route: route.abort())
```

### Taking Screenshots

```python
def _take_screenshot(self, page, name):
    """Take a screenshot of the page."""
    page.screenshot(path=f"screenshots/{name}.png")
```

### Handling Infinite Scroll

```python
def _scroll_to_bottom(self, page):
    """Scroll to the bottom of the page to load more content."""
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)  # Wait for content to load
```

## Best Practices

1. **Resource Management**: Always clean up Playwright resources in a `finally` block
2. **Error Handling**: Implement robust error handling for network issues
3. **Rate Limiting**: Add delays between requests to avoid being blocked
4. **User Agent Rotation**: Consider rotating user agents for each request
5. **Proxy Support**: Use proxies for high-volume scraping

## Testing with Playwright

You can also use Playwright for testing your crawlers:

```python
from playwright.sync_api import expect

def test_crawler():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Test the crawler's URL extraction
        page.goto("https://example.com/football")
        links = page.query_selector_all("a")
        
        # Verify that article links are found
        article_links = [link for link in links if 'article' in link.get_attribute("href")]
        expect(len(article_links)).to_be_greater_than(0)
        
        browser.close()
```

## References

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Playwright Python API](https://playwright.dev/python/docs/api/class-playwright)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices) 