from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NewsCreate(BaseModel):
    title: str
    content: str
    hyperlink: Optional[str] = None
    publish_date: datetime

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    hyperlink: Optional[str] = None
    publish_date: Optional[datetime] = None

class NewsResponse(BaseModel):
    id: int
    title: str
    content: str
    image_url: Optional[str] = None
    hyperlink: Optional[str] = None
    publish_date: datetime

    class Config:
        from_attributes = True