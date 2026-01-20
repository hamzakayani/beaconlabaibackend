from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReorderNewsRequest(BaseModel):
    order: int

class NewsCreate(BaseModel):
    title: str
    content: str
    hyperlink: Optional[str] = None
    publish_date: datetime
    order: int = 1

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    hyperlink: Optional[str] = None
    publish_date: Optional[datetime] = None
    order: Optional[int] = None

class NewsResponse(BaseModel):
    id: int
    title: str
    content: str
    image_url: Optional[str] = None
    hyperlink: Optional[str] = None
    publish_date: datetime
    order: int

    class Config:
        from_attributes = True