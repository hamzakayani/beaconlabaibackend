from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LabGalleryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    image_url: Optional[str] = None
    order: int = 1


class LabGalleryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    image_url: Optional[str] = None
    order: Optional[int] = None


class LabGalleryResponse(BaseModel):
    id: int
    title: str
    content: str
    image_url: Optional[str] = None
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
