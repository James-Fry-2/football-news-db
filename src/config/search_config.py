"""
Configuration for enhanced search service weights and parameters.
"""

class SearchConfig:
    """Configuration class for search model weights and parameters."""
    
    # Source credibility weights
    SOURCE_WEIGHTS = {
        "BBC Sport": 1.0,
        "Sky Sports": 0.95,
        "Guardian": 0.95,
        "Telegraph": 0.9,
        "Fantasy Football Scout": 0.85,
        "ESPN": 0.8,
    }
     
    # Default source weight for unknown sources
    DEFAULT_SOURCE_WEIGHT = 0.7
    
    # Time decay parameters
    TEMPORAL_DECAY_RATE = 0.1  # For temporal-only strategy
    HYBRID_DECAY_RATE = 0.05   # For hybrid strategy (slower decay)
    DEFAULT_TIME_DECAY = 0.5   # For articles without dates
    
    # Content quality parameters
    OPTIMAL_CONTENT_LENGTH_MIN = 500
    OPTIMAL_CONTENT_LENGTH_MAX = 2000
    MIN_TITLE_LENGTH = 20
    MAX_TITLE_LENGTH = 150
    CLICKBAIT_PENALTY = 0.7
    
    # Clickbait detection patterns
    #TODO: Improve clickbait detection patterns
    CLICKBAIT_PATTERNS = [
        r"\d+\s+(things|ways|reasons|facts)",
        r"you won't believe",
        r"shocking",
        r"amazing",
        r"incredible"
    ]
    
    # Sentiment scoring parameters
    NEUTRAL_SENTIMENT_BASE = 0.5
    POSITIVE_SENTIMENT_MULTIPLIER = 0.3
    NEGATIVE_SENTIMENT_MULTIPLIER = 0.2
    
    # Scoring strategy weights
    SCORING_WEIGHTS = {
        "semantic_only": {
            "semantic": 1.0
        },
        "temporal": {
            "semantic": 0.6,
            "temporal": 0.3,
            "text_relevance": 0.1
        },
        "engagement": {
            "semantic": 0.5,
            "source_credibility": 0.2,
            "content_quality": 0.15,
            "text_relevance": 0.1,
            "sentiment": 0.05
        },
        "hybrid": {
            "semantic": 0.4,
            "temporal": 0.25,
            "source_credibility": 0.15,
            "text_relevance": 0.1,
            "content_quality": 0.07,
            "sentiment": 0.03
        }
    }
    
    # Text relevance parameters
    TITLE_MATCH_WEIGHT = 2.0  # Title matches weighted 2x more than content matches 