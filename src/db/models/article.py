from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class Article(BaseModel):
    url: str = Field(..., description="Unique URL of the article")
    title: str = Field(..., description="Title of the article")
    content: str = Field(..., description="Main content of the article")
    published_date: datetime = Field(..., description="Publication date of the article")
    source: str = Field(..., description="Source of the article (e.g., 'BBC', 'Sky Sports')")
    teams: List[str] = Field(default_factory=list, description="List of teams mentioned in the article")
    players: List[str] = Field(default_factory=list, description="List of players mentioned in the article")
    summary: Optional[str] = Field(None, description="Optional summary of the article")
    image_url: Optional[str] = Field(None, description="Optional URL of the article's main image")
    author: Optional[str] = Field(None, description="Optional author of the article")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the article was added to the database")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the article was last updated in the database")

    class Config:
        schema_extra = {
            "example": {
                "url": "https://www.bbc.com/sport/football/article123",
                "title": "Premier League: Latest Transfer News",
                "content": "Full article content here...",
                "published_date": "2024-03-20T10:00:00Z",
                "source": "BBC",
                "teams": ["Manchester United", "Liverpool"],
                "players": ["Marcus Rashford", "Mohamed Salah"],
                "summary": "Latest transfer news from the Premier League",
                "image_url": "https://example.com/image.jpg",
                "author": "John Smith",
                "created_at": "2024-03-20T10:30:00Z",
                "updated_at": "2024-03-20T10:30:00Z"
            }
        } 