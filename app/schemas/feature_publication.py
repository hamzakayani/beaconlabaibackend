from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReorderFeaturePublicationRequest(BaseModel):
    order: int

# Request Schemas

class DOIFeaturePublicationCreate(BaseModel):
    doi: str
    nct_number: Optional[str] = None
    is_presentation: bool= False
    order: int = 1

class PubmedFeaturePublicationCreate(BaseModel):
    pm_id: str 
    nct_number: Optional[str] = None
    is_presentation: bool= False
    order: int = 1
class ManualFeaturePublicationCreate(BaseModel):
    title: str
    abstract: Optional[str] 
    authers: Optional[str] 
    journal: Optional[str] 
    publish_date: Optional[str] 
    pubmed_id: Optional[str] 
    nct_number: Optional[str] 
    doi: Optional[str] 
    is_presentation: bool= False
    order: int = 1

class FeaturePublicationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    abstract: Optional[str] = None
    authers: Optional[str] = None
    journal: Optional[str] = None
    publish_date: Optional[str] = None
    pubmed_id: Optional[str] = None
    nct_number: Optional[str] = None
    doi: Optional[str] = None
    is_presentation: Optional[bool] = None
    order: Optional[int] = None

# Response Schema
class FeaturePublicationResponse(BaseModel):
    id: int
    image_url: Optional[str] = None
    title: str
    abstract: str
    authers: str
    journal: str
    publish_date: str
    pubmed_id: str
    nct_number: str
    doi: str
    is_presentation: bool
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
