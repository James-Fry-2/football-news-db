from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

class Article(BaseModel):
    url: HttpUrl = Field(..., description="The source URL of the article")
    title: str = Field(..., description="Article headline")
    content: str = Field(..., description="Full article content")
    source: str = Field(..., description="News source (e.g., 'BBC Sport', 'Sky Sports')")
    published_date: datetime = Field(..., description="Article publication date")
    
    # Metadata
    author: Optional[str] = Field(None, description="Article author if available")
    category: List[str] = Field(default_factory=list, description="Article categories")
    tags: List[str] = Field(default_factory=list, description="Article tags")
    
    # Analysis fields
    sentiment_score: Optional[float] = Field(None, description="Article sentiment score")
    mentioned_players: List[str] = Field(default_factory=list, description="Players mentioned in the article")
    mentioned_teams: List[str] = Field(default_factory=list, description="Teams mentioned in the article")
    
    # Processing metadata
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "url": "https://www.bbc.com/sport/football/article-1",
                "title": "Liverpool secure dramatic win against Manchester United",
                "content": "Full article content here...",
                "source": "BBC Sport",
                "published_date": "2024-04-24T10:00:00Z",
                "author": "John Smith",
                "category": ["Premier League", "Match Report"],
                "tags": ["Liverpool", "Manchester United", "Premier League"],
                "sentiment_score": 0.8,
                "mentioned_players": ["Mohamed Salah", "Bruno Fernandes"],
                "mentioned_teams": ["Liverpool", "Manchester United"]
            }
        } 