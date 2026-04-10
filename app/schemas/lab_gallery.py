from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LabGalleryCategory(str, Enum):
    CONFERENCES = "conferences"
    DINNERS_AND_CELEBRATIONS = "dinners_and_celebrations"
    CULTURAL_EVENTS = "cultural_events"
    FAREWELLS = "farewells"
    MATCH_CELEBRATIONS = "match_celebrations"
    VISITING_FACULTY = "visiting_faculty"


class LabGalleryStatus(str, Enum):
    ONGOING = "ongoing"
    UPCOMING = "upcoming"
    PAST = "past"
    COMPLETED = "completed"
    DONE = "done"


class LabGalleryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    image_url: Optional[str] = None
    order: int = 1
    category: LabGalleryCategory
    date: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=255)
    participant: str = Field(..., min_length=1, max_length=100)
    status: LabGalleryStatus


class LabGalleryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    image_url: Optional[str] = None
    order: Optional[int] = None
    category: Optional[LabGalleryCategory] = None
    date: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    participant: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[LabGalleryStatus] = None


class LabGalleryResponse(BaseModel):
    id: int
    title: str
    content: str
    image_url: Optional[str] = None
    order: int
    category: LabGalleryCategory
    date: str
    location: str
    participant: str
    status: LabGalleryStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
