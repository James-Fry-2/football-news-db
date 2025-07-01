#!/usr/bin/env python3
"""
Test script for the Football Cache Key Generator

This script demonstrates how the new semantic cache key generator handles
variations in football queries and creates consistent keys for similar content.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db.services.llm_service import FootballCacheKeyGenerator

def test_team_variations():
    """Test how team name variations are normalized."""
    print("=== TEAM NAME VARIATIONS ===")
    
    test_queries = [
        "What is Man United's current form?",
        "Tell me about Manchester United's recent performance",
        "How is MUFC doing this season?",
        "Man City vs Arsenal predictions",
        "Manchester City against Arsenal match analysis",
        "Spurs latest news",
        "Tottenham transfer rumors",
        "Liverpool vs Reds comparison"  # This should normalize 'Reds' to Liverpool
    ]
    
    for query in test_queries:
        entities = FootballCacheKeyGenerator.extract_entities(query)
        cache_key = FootballCacheKeyGenerator.generate_semantic_cache_key(
            query=query,
            category="news"
        )
        
        print(f"\nQuery: {query}")
        print(f"Teams found: {list(entities['teams'])}")
        print(f"Cache key: {cache_key}")

def test_player_variations():
    """Test how player name variations are normalized."""
    print("\n\n=== PLAYER NAME VARIATIONS ===")
    
    test_queries = [
        "Haaland's goal stats this season",
        "How many goals has Erling Haaland scored?",
        "Tell me about Salah's performance",
        "Mo Salah FPL value",
        "Mohamed Salah latest news",
        "KDB assists this season",
        "Kevin De Bruyne injury update",
        "CR7 transfer rumors",
        "Cristiano Ronaldo career stats"
    ]
    
    for query in test_queries:
        entities = FootballCacheKeyGenerator.extract_entities(query)
        cache_key = FootballCacheKeyGenerator.generate_semantic_cache_key(
            query=query,
            category="factual"
        )
        
        print(f"\nQuery: {query}")
        print(f"Players found: {list(entities['players'])}")
        print(f"Cache key: {cache_key}")

def test_intent_classification():
    """Test how different query intents are classified."""
    print("\n\n=== INTENT CLASSIFICATION ===")
    
    test_queries = [
        ("Harry Kane stats this season", "stats"),
        ("Latest Arsenal transfer news", "news"),
        ("Who is better: Messi or Ronaldo?", "comparison"),
        ("Best FPL captain this week", "fpl"),
        ("Chelsea squad for tonight's match", "team_info"),
        ("When is the Liverpool vs City game?", "match")
    ]
    
    for query, expected_intent in test_queries:
        entities = FootballCacheKeyGenerator.extract_entities(query)
        cache_key = FootballCacheKeyGenerator.generate_semantic_cache_key(
            query=query,
            category="opinion"
        )
        
        print(f"\nQuery: {query}")
        print(f"Expected intent: {expected_intent}")
        print(f"Detected intents: {list(entities['intents'])}")
        print(f"Cache key: {cache_key}")

def test_context_awareness():
    """Test how conversation context affects cache keys."""
    print("\n\n=== CONTEXT AWARENESS ===")
    
    base_query = "What about his recent form?"
    
    contexts = [
        ["Tell me about Harry Kane", "He's been scoring well"],
        ["How is Salah doing?", "His assists are good too"],
        ["Manchester United transfers", "They need a striker"]
    ]
    
    for i, context in enumerate(contexts):
        cache_key = FootballCacheKeyGenerator.generate_semantic_cache_key(
            query=base_query,
            context_messages=context,
            category="factual"
        )
        
        print(f"\nContext {i+1}: {context}")
        print(f"Query: {base_query}")
        print(f"Cache key: {cache_key}")

def test_cache_sharing():
    """Test which queries would share cache."""
    print("\n\n=== CACHE SHARING ANALYSIS ===")
    
    query_pairs = [
        ("Haaland goals this season", "Erling Haaland goal statistics"),
        ("Man United vs Arsenal", "Manchester United against Arsenal prediction"),
        ("Best FPL players", "Top fantasy football picks"),
        ("Chelsea news", "Liverpool transfer updates"),
        ("Messi stats", "Ronaldo performance")
    ]
    
    for query1, query2 in query_pairs:
        would_share = FootballCacheKeyGenerator.should_share_cache(query1, query2)
        
        entities1 = FootballCacheKeyGenerator.extract_entities(query1)
        entities2 = FootballCacheKeyGenerator.extract_entities(query2)
        
        print(f"\nQuery 1: {query1}")
        print(f"Query 2: {query2}")
        print(f"Would share cache: {would_share}")
        print(f"Q1 entities: teams={list(entities1['teams'])}, players={list(entities1['players'])}, intents={list(entities1['intents'])}")
        print(f"Q2 entities: teams={list(entities2['teams'])}, players={list(entities2['players'])}, intents={list(entities2['intents'])}")

def test_normalization():
    """Test query text normalization."""
    print("\n\n=== QUERY NORMALIZATION ===")
    
    test_queries = [
        "What is the best team in the Premier League?",
        "Tell me about Harry Kane's goal scoring record",
        "When will Manchester United play against Arsenal?",
        "How much does Haaland cost in FPL?",
        "Who should I captain this week for fantasy football?"
    ]
    
    for query in test_queries:
        normalized = FootballCacheKeyGenerator.normalize_query_text(query)
        
        print(f"\nOriginal: {query}")
        print(f"Normalized: {normalized}")

def main():
    """Run all tests."""
    print("FOOTBALL CACHE KEY GENERATOR TEST")
    print("=" * 50)
    
    test_team_variations()
    test_player_variations()
    test_intent_classification()
    test_context_awareness()
    test_cache_sharing()
    test_normalization()
    
    print("\n\n" + "=" * 50)
    print("TEST COMPLETED")
    print("\nKey benefits of this cache key generator:")
    print("1. Normalizes team/player name variations (Man United = Manchester United)")
    print("2. Extracts query intent for better categorization")
    print("3. Uses conversation context to improve cache hits")
    print("4. Creates consistent keys for semantically similar queries")
    print("5. Enables intelligent cache sharing between related queries")

if __name__ == "__main__":
    main() 