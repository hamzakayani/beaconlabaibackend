from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class ReorderJobRequest(BaseModel):
    order: int

class JobTypeEnum(str, Enum):
    full_time = "full_time"
    part_time = "part_time"
    remote = "remote"
    hybrid = "hybrid"
    contract = "contract"


class JobStatusEnum(str, Enum):
    open = "open"
    closed = "closed"
    draft = "draft"


# Job Schemas
class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    job_type: JobTypeEnum
    location: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    status: JobStatusEnum = JobStatusEnum.draft
    funded_by: Optional[str] = Field(None, max_length=255)
    visa_type: Optional[str] = Field(None, max_length=255)
    job_tenure: Optional[str] = Field(None, max_length=255)
    required_qualifications: Optional[str] = None
    preferred_qualifications: Optional[str] = None
    order: int = 1


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    job_type: Optional[JobTypeEnum] = None
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[JobStatusEnum] = None
    funded_by: Optional[str] = Field(None, max_length=255)
    visa_type: Optional[str] = Field(None, max_length=255)
    job_tenure: Optional[str] = Field(None, max_length=255)
    required_qualifications: Optional[str] = None
    preferred_qualifications: Optional[str] = None
    order: Optional[int] = None

class JobResponse(BaseModel):
    id: int
    title: str
    job_type: JobTypeEnum
    location: str
    description: str
    status: JobStatusEnum
    funded_by: Optional[str]
    visa_type: Optional[str]
    job_tenure: Optional[str]
    required_qualifications: Optional[str]
    preferred_qualifications: Optional[str]
    order: int
    class Config:
        from_attributes = True


# Job Application Schemas
# class JobApplicationCreate(BaseModel):
#     full_name: str = Field(..., min_length=1, max_length=255)
#     email: EmailStr
#     phone: Optional[str] = Field(None, max_length=50)
#     cover_letter: Optional[str] = None


class JobApplicationResponse(BaseModel):
    id: int
    job_id: int
    full_name: str
    email: str
    phone: Optional[str]
    cover_letter: Optional[str]
    cv_file_path: str

    class Config:
        from_attributes = True