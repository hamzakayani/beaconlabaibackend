from typing import Optional
from pydantic import BaseModel

class DOIPaperCreate(BaseModel):
    doi: str
    nct_number: Optional[str] = None

class PubmedPaperCreate(BaseModel):
    pm_id: str 
    nct_number: Optional[str] = None

class ManualPaperCreate(BaseModel):
    title: str
    abstract: Optional[str] = None
    authers: Optional[str] = None
    journal: Optional[str] = None
    paper_id: Optional[str] = None
    publish_date: Optional[str] = None
    pubmed_id: Optional[str] = None
    nct_number: Optional[str] = None
    doi: Optional[str] = None

class PaperResponse(BaseModel):
    id: int
    title: str
    abstract: str
    authers: str
    journal: str
    paper_id: str
    publish_date: str
    pubmed_id: str
    nct_number: str
    tags: dict
    doi: str

    class Config:
        from_attributes = True