from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
from app.models.contact_enums import ContactSubjectEnum
from app.schemas.pagination import PaginatedResponse, PageInfo

# Request Schemas
class ContactFormCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: Optional[EmailStr] = Field(None, min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    subject: ContactSubjectEnum
    message: Optional[str] = Field(None, min_length=1, max_length=5000)

    # @field_validator('phone_number')
    # @classmethod
    # def validate_phone(cls, v: Optional[str]) -> Optional[str]:
    #     if v is None:
    #         return v
    #     # Remove common phone number formatting characters
    #     cleaned = ''.join(filter(str.isdigit, v))
    #     if len(cleaned) < 10:
    #         raise ValueError('Phone number must contain at least 10 digits')
    #     return v

class ContactInquiryUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    subject: Optional[ContactSubjectEnum] = None
    message: Optional[str] = Field(None, min_length=1, max_length=5000)

    # @field_validator('phone_number')
    # @classmethod
    # def validate_phone(cls, v: Optional[str]) -> Optional[str]:
    #     if v is None:
    #         return v
    #     cleaned = ''.join(filter(str.isdigit, v))
    #     if len(cleaned) < 10:
    #         raise ValueError('Phone number must contain at least 10 digits')
    #     return v

# Response Schemas
class ContactInquiryResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    subject: ContactSubjectEnum
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True




class ContactInfoResponse(BaseModel):
    email: str
    address: str

# Paginated Response
class ContactInquiryListResponse(PaginatedResponse[ContactInquiryResponse]):
    pass

