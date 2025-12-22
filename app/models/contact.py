from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, Enum
from app.db.database import Base
from app.models.contact_enums import ContactSubjectEnum
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class ContactInquiry(Base):
    __tablename__ = "contact_inquiries"

    id = Column(Integer, primary_key=True,autoincrement=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    subject = Column(Enum(ContactSubjectEnum), nullable=False,default="")
    message = Column(Text, nullable=False,default="")
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

