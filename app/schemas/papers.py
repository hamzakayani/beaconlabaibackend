from typing import List, Optional
from enum import Enum
from pydantic import BaseModel

class ReorderPaperRequest(BaseModel):
    order: int

class Category(str, Enum):
    bioinformatics = "bioinformatics"
    artificial_intelligence = "artificial intelligence"
    evidence_synthesis = "evidence synthesis"
    oncology = "oncology"
    genomics = "genomics"

class DOIPaperCreate(BaseModel):
    doi: str
    nct_number: Optional[str] = None
    category: Optional[List[Category]] = None
    is_presentation: Optional[bool] = False
    order: int = 1
    is_open: bool = False
class PubmedPaperCreate(BaseModel):
    pm_id: str 
    nct_number: Optional[str] = None
    category: Optional[List[Category]] = None
    is_presentation: Optional[bool] = False
    order: int = 1
    is_open: bool = False

class ManualPaperCreate(BaseModel):
    title: str
    abstract: Optional[str] = None
    authers: Optional[str] = None
    journal: Optional[str] = None
    publish_date: Optional[str] = None
    pubmed_id: Optional[str] = None
    nct_number: Optional[str] = None
    doi: Optional[str] = None
    category: Optional[List[Category]] = None
    is_presentation: Optional[bool] = False
    order: int = 1
    is_open: bool = False
class PaperUpdate(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    authers: Optional[str] = None
    journal: Optional[str] = None
    publish_date: Optional[str] = None
    pubmed_id: Optional[str] = None
    nct_number: Optional[str] = None
    doi: Optional[str] = None
    category: Optional[List[Category]] = None
    order: Optional[int] = None
    is_presentation: Optional[bool] = None
    is_open: Optional[bool] = None
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
    category: Optional[List[Category]] = None
    order: int
    is_presentation: bool
    is_open: bool
    class Config:
        from_attributes = True