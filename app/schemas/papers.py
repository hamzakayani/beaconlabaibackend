from typing import Optional
from enum import Enum
from pydantic import BaseModel

class ReorderPaperRequest(BaseModel):
    order: int

class Category(str, Enum):
    bioinformatics = "bioinformatics"
    artificial_intelligence = "artificial intelligence"
    evidence_synthesis = "evidence synthesis"
    oncology = "oncology"

class DOIPaperCreate(BaseModel):
    doi: str
    nct_number: Optional[str] = None
    category: Optional[Category] = None
    order: int = 1

class PubmedPaperCreate(BaseModel):
    pm_id: str 
    nct_number: Optional[str] = None
    category: Optional[Category] = None
    order: int = 1

class ManualPaperCreate(BaseModel):
    title: str
    abstract: Optional[str] = None
    authers: Optional[str] = None
    journal: Optional[str] = None
    publish_date: Optional[str] = None
    pubmed_id: Optional[str] = None
    nct_number: Optional[str] = None
    doi: Optional[str] = None
    category: Optional[Category] = None
    order: int = 1

class PaperUpdate(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    authers: Optional[str] = None
    journal: Optional[str] = None
    publish_date: Optional[str] = None
    pubmed_id: Optional[str] = None
    nct_number: Optional[str] = None
    doi: Optional[str] = None
    category: Optional[Category] = None
    order: Optional[int] = None


class PaperResponse(BaseModel):
    id: int
    title: str
    abstract: str
    authers: str
    journal: str
    publish_date: str
    pubmed_id: str
    nct_number: str
    tags: dict
    doi: str
    category: Optional[str] = None
    order: int

    class Config:
        from_attributes = True