from typing import Optional
from pydantic import BaseModel

class DOIPaperCreate(BaseModel):
    doi: str
    nct_number: Optional[str] = ""

class PubmedPaperCreate(BaseModel):
    pm_id: str 
    nct_number: Optional[str] = None

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