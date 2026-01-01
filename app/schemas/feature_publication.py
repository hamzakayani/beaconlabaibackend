from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.schemas.papers import DOIPaperCreate, PubmedPaperCreate

# Request Schemas
class ManualFeaturePublicationCreate(BaseModel):
    title: str
    abstract: Optional[str] 
    authers: Optional[str] 
    journal: Optional[str] 
    paper_id: Optional[str] 
    publish_date: Optional[str] 
    pubmed_id: Optional[str] 
    nct_number: Optional[str] 
    doi: Optional[str] 


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

