from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum
from app.schemas.pagination import PaginatedResponse, PageInfo

class ReorderTeamMemberRequest(BaseModel):
    order: int

class TeamCategory(str, Enum):
    LAB_DIRECTOR = "lab director"
    COLLABORATIONS = "collaborations"
    LAB_MEMBERS = "lab members"
    LAB_ALUMNI = "lab alumni"
    CLINICAL_RESIDENT_AND_FELLOWS = "clinical resident and fellows"
    GRADUATE_AND_UNDERGRADUATE_STUDENTS = "graduate and undergraduate students"
    MEDICAL_STUDENTS = "medical students"
    VISITING_STUDENTS_AND_FELLOWS = "visiting student and fellows"
    RESEARCH_TRAINEE_AND_FELLOWS = "research trainee and fellows"

class TeamMemberResponse(BaseModel):
    id: int
    name: str
    category: TeamCategory
    role: str
    designation: str
    description: str
    image_url: Optional[str] = None
    hyperlink: Optional[str] = None
    order: int

    class Config:
        from_attributes = True



