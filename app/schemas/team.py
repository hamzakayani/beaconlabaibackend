from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum
from app.schemas.pagination import PaginatedResponse, PageInfo

class TeamCategory(str, Enum):
    LAB_DIRECTOR = "lab director"
    COLLABORATIONS = "collaborations"
    LAB_MEMBERS = "lab members"
    LAB_ALUMNI = "lab alumni"
    CLINICAL_RESIDENT_AND_FELLOWS = "clinical resident and fellows"
    GRADUATE_AND_UNDERGRADUATE_STUDENTS = "graduate and undergraduate students"
    MEDICAL_STUDENTS = "medical students"

# # Request Schemas
# class TeamMemberCreate(BaseModel):
#     name: str = Field(..., min_length=1, max_length=50)
#     category: TeamCategory
#     role: str = Field(..., min_length=1, max_length=50)
#     designation: str = Field(..., min_length=1, max_length=50)
#     description: Optional[str] = Field(None, min_length=1)
#     image_url: Optional[str] = Field(None, max_length=255)
#     hyperlink: Optional[str] = Field(None, max_length=255)

class TeamMemberUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    category: Optional[TeamCategory] = None
    role: Optional[str] = Field(None, min_length=1, max_length=50)
    designation: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1)
    image_url: Optional[str] = Field(None, max_length=255)
    hyperlink: Optional[str] = Field(None, max_length=255)

# Response Schemas
class TeamMemberResponse(BaseModel):
    id: int
    name: str
    category: TeamCategory
    role: str
    designation: str
    description: str
    image_url: str
    hyperlink: str

    class Config:
        from_attributes = True



