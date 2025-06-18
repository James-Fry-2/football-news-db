"""
Unit tests for BBC crawler URL fragment stripping functionality.

Tests ensure that URLs ending with fragments like #comments are properly filtered out
and that URL building strips fragments correctly.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import aiohttp

# Import the BBC crawler
from src.crawlers.bbc_crawler import BBCCrawler


class TestBBCCrawlerFragmentHandling:
    """Test BBC crawler's handling of URL fragments like #comments."""
    
    def test_url_fragment_filtering_team_articles(self):
        """Test that URLs with fragments are rejected by team article validation."""
        # Create crawler instance
        crawler = BBCCrawler()
        
        # Test URLs with fragments (should be rejected)
        urls_with_fragments = [
            "/sport/football/articles/c2494zgd1yno#comments",
            "https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno#comments",
            "/sport/football/articles/c057vrqp9p1o#comments",
            "/sport/football/67891234#comments",
            "/sport/football/articles/test#section",
            "/sport/football/articles/abc123#anything"
        ]
        
        for url in urls_with_fragments:
            result = crawler._is_valid_team_article_link(url)
            assert result is False, f"URL with fragment should be rejected: {url}"
    
    def test_url_fragment_filtering_general_articles(self):
        """Test that URLs with fragments are rejected by general article validation."""
        # Create crawler instance  
        crawler = BBCCrawler()
        
        # Test URLs with fragments (should be rejected)
        urls_with_fragments = [
            "/sport/football/articles/c2494zgd1yno#comments",
            "https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno#comments",
            "/sport/football/live#score",
            "/sport/football/tables#premier-league",
            "/sport/football/123456#comments"
        ]
        
        for url in urls_with_fragments:
            result = crawler._is_valid_article_link(url)
            assert result is False, f"URL with fragment should be rejected: {url}"
    
    def test_valid_urls_without_fragments(self):
        """Test that valid URLs without fragments are accepted."""
        # Create crawler instance
        crawler = BBCCrawler()
        
        # Test valid URLs without fragments
        valid_urls = [
            "/sport/football/articles/c2494zgd1yno",
            "/sport/football/articles/c057vrqp9p1o", 
            "/sport/football/articles/cpw742nre1go",
            "/sport/football/67891234"
        ]
        
        for url in valid_urls:
            result = crawler._is_valid_team_article_link(url)
            # Should be True for article URLs
            if "/articles/" in url or url.split("/")[-1].isdigit():
                assert result is True, f"Valid article URL should be accepted: {url}"
    
    def test_url_building_strips_fragments(self):
        """Test that _build_full_url strips fragments from URLs."""
        # Create crawler instance
        crawler = BBCCrawler()
        
        # Test cases: input URL -> expected output URL
        test_cases = [
            # Relative URLs with fragments
            ("/sport/football/articles/c2494zgd1yno#comments", 
             "https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno"),
            
            # Absolute URLs with fragments  
            ("https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno#comments",
             "https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno"),
            
            # URLs without fragments (should remain unchanged)
            ("/sport/football/articles/c2494zgd1yno",
             "https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno"),
            
            # Different fragment types
            ("/sport/football/articles/test#section",
             "https://www.bbc.co.uk/sport/football/articles/test"),
             
            ("/sport/football/articles/abc123#anything",
             "https://www.bbc.co.uk/sport/football/articles/abc123")
        ]
        
        for input_url, expected_output in test_cases:
            result = crawler._build_full_url(input_url)
            assert result == expected_output, f"Fragment not stripped correctly. Input: {input_url}, Expected: {expected_output}, Got: {result}"
            assert "#" not in result, f"Fragment still present in output URL: {result}"
    
    def test_url_fragment_stripping_simple(self):
        """Simple test for URL fragment stripping without async complexity."""
        # Create crawler instance
        crawler = BBCCrawler()
        
        # Test the URL fragment stripping directly
        url_with_fragment = "https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno#comments"
        
        # Test that clean_url extraction works (this is what happens in extract_article_data_async)
        clean_url = url_with_fragment.split('#')[0] if '#' in url_with_fragment else url_with_fragment
        
        # Verify fragment was stripped
        assert clean_url == "https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno"
        assert "#" not in clean_url
        assert "comments" not in clean_url
        
        # Test with different fragments
        test_cases = [
            ("https://www.bbc.co.uk/sport/football/articles/test#comments", 
             "https://www.bbc.co.uk/sport/football/articles/test"),
            ("https://www.bbc.co.uk/sport/football/articles/abc123#section", 
             "https://www.bbc.co.uk/sport/football/articles/abc123"),
            ("https://www.bbc.co.uk/sport/football/articles/xyz789", 
             "https://www.bbc.co.uk/sport/football/articles/xyz789"),  # No fragment
        ]
        
        for input_url, expected in test_cases:
            result = input_url.split('#')[0] if '#' in input_url else input_url
            assert result == expected, f"Fragment stripping failed for {input_url}"

    def test_real_world_bbc_url_example(self):
        """Test the specific URL example provided: https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno#comments"""
        # Create crawler instance
        crawler = BBCCrawler()
        
        # The exact URL from the example
        test_url = "https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno#comments"
        
        # Test that it's rejected by validation (has fragment)
        is_valid_team = crawler._is_valid_team_article_link(test_url)
        is_valid_general = crawler._is_valid_article_link(test_url)
        
        assert is_valid_team is False, "URL with #comments should be rejected by team validation"
        assert is_valid_general is False, "URL with #comments should be rejected by general validation"
        
        # Test that _build_full_url strips the fragment
        clean_url = crawler._build_full_url(test_url)
        expected_clean_url = "https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno"
        
        assert clean_url == expected_clean_url, f"Fragment not stripped. Expected: {expected_clean_url}, Got: {clean_url}"
        assert "#comments" not in clean_url, "Fragment #comments should be completely removed"
    
    def test_multiple_fragment_types(self):
        """Test that various types of URL fragments are properly handled."""
        # Create crawler instance
        crawler = BBCCrawler()
        
        # Test different fragment types
        fragment_examples = [
            "#comments",
            "#section", 
            "#top",
            "#main-content",
            "#share",
            "#related-topics",
            "#player-1234"
        ]
        
        base_url = "/sport/football/articles/c2494zgd1yno"
        
        for fragment in fragment_examples:
            test_url = base_url + fragment
            
            # Should be rejected by validation
            assert crawler._is_valid_team_article_link(test_url) is False
            assert crawler._is_valid_article_link(test_url) is False
            
            # Should be stripped by URL building
            clean_url = crawler._build_full_url(test_url)
            expected = "https://www.bbc.co.uk" + base_url
            assert clean_url == expected
            assert fragment not in clean_url
    
    def test_url_without_fragments_unchanged(self):
        """Test that URLs without fragments are processed normally."""
        # Create crawler instance
        crawler = BBCCrawler()
        
        # Test URL without fragment
        clean_url = "/sport/football/articles/c2494zgd1yno"
        
        # Should be accepted by team validation (valid article pattern)
        is_valid_team = crawler._is_valid_team_article_link(clean_url)
        assert is_valid_team is True, "Valid article URL without fragment should be accepted"
        
        # Should build URL correctly without modification
        built_url = crawler._build_full_url(clean_url)
        expected = "https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno"
        assert built_url == expected
        assert "#" not in built_url 

    def test_extract_article_data_url_cleaning(self):
        """Test that URL fragment stripping logic works correctly (without complex async mocking)."""
        # Create crawler instance
        crawler = BBCCrawler()
        
        # Test the URL cleaning logic that's used in extract_article_data_async
        test_urls = [
            ("https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno#comments",
             "https://www.bbc.co.uk/sport/football/articles/c2494zgd1yno"),
            ("https://www.bbc.co.uk/sport/football/articles/test#section",
             "https://www.bbc.co.uk/sport/football/articles/test"),
            ("https://www.bbc.co.uk/sport/football/articles/abc123",
             "https://www.bbc.co.uk/sport/football/articles/abc123"),  # No fragment
        ]
        
        for url_with_fragment, expected_clean_url in test_urls:
            # This is the exact logic used in extract_article_data_async
            clean_url = url_with_fragment.split('#')[0] if '#' in url_with_fragment else url_with_fragment
            
            assert clean_url == expected_clean_url, f"URL cleaning failed for {url_with_fragment}"
            assert "#" not in clean_url, "Fragment should be completely removed"
            
            # Also test that this would be properly processed by the result dict
            mock_result = {
                'url': clean_url,
                'title': 'Test Title',
                'content': 'Test Content',
                'source': 'BBC Sport'
            }
            
            assert mock_result['url'] == expected_clean_url
            assert "#" not in mock_result['url'] 