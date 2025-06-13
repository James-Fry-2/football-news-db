"""
Centralized crawler registry to avoid code duplication.
This module maintains a single source of truth for all available crawlers.
"""

from typing import Dict, Type
from .bbc_crawler import BBCCrawler
from .ffs_crawler import FFSCrawler
from .goal_crawler import GoalNewsPlaywrightCrawler
from .goal_crawler_requests import GoalNewsRequestsCrawler

# Central registry of all available crawlers
CRAWLERS: Dict[str, Type] = {
    'bbc': BBCCrawler,
    'ffs': FFSCrawler,
    'goal': GoalNewsPlaywrightCrawler,
    'goal_requests': GoalNewsRequestsCrawler,
}

def get_crawler_class(name: str):
    """
    Get a crawler class by name.
    
    Args:
        name: Name of the crawler
        
    Returns:
        Crawler class or None if not found
    """
    return CRAWLERS.get(name)

def get_available_crawlers():
    """
    Get list of available crawler names.
    
    Returns:
        List of crawler names
    """
    return list(CRAWLERS.keys())

def is_valid_crawler(name: str) -> bool:
    """
    Check if a crawler name is valid.
    
    Args:
        name: Name to check
        
    Returns:
        True if valid crawler name
    """
    return name in CRAWLERS 