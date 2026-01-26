from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NewsResponse(BaseModel):
    id: int
    title: str
    content: str
    image_url: Optional[str] = None
    hyperlink: Optional[str] = None
    publish_date: datetime
    order: int
    is_open: bool
    class Config:
        from_attributes = True