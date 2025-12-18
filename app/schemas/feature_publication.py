from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.schemas.papers import DOIPaperCreate, PubmedPaperCreate

# Request Schemas
class ManualFeaturePublicationCreate(BaseModel):
    title: str = Field(..., min_length=1)
    abstract: Optional[str] = Field(..., min_length=1)
    authers: Optional[str] = Field(..., min_length=1)
    journal: Optional[str] = Field(..., min_length=1)
    paper_id: Optional[str] = Field(..., min_length=1)
    publish_date: Optional[str] = Field(..., min_length=1)
    pubmed_id: Optional[str] = Field(..., min_length=1)
    nct_number: Optional[str] = Field(..., min_length=1)
    doi: Optional[str] = Field(..., min_length=1)


class FeaturePublicationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    abstract: Optional[str] = None
    authers: Optional[str] = None
    journal: Optional[str] = None
    paper_id: Optional[str] = None
    publish_date: Optional[str] = None
    pubmed_id: Optional[str] = None
    nct_number: Optional[str] = None
    doi: Optional[str] = None


# Response Schema
class FeaturePublicationResponse(BaseModel):
    id: int
    image_url: Optional[str] = None
    title: str
    abstract: str
    authers: str
    journal: str
    paper_id: str
    publish_date: str
    pubmed_id: str
    nct_number: str
    doi: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

