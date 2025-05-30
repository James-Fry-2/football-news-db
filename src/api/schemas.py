from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List, Optional

class ArticleBase(BaseModel):
    title: str
    url: HttpUrl
    content: str
    summary: Optional[str] = None
    published_date: datetime
    source: str
    author: Optional[str] = None
    status: str = 'active'

class ArticleCreate(ArticleBase):
    pass

class ArticleUpdate(ArticleBase):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    published_date: Optional[datetime] = None
    source: Optional[str] = None
    author: Optional[str] = None
    status: Optional[str] = None

class Article(ArticleBase):
    id: int
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True 