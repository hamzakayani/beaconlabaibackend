from pydantic import BaseModel

class DOIPaperCreate(BaseModel):
    doi: str
    nct_number: str = ""
