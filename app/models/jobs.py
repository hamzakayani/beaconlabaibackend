from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, Enum as SQLEnum
from app.db.database import Base
from datetime import datetime, timezone
from app.schemas.jobs import JobTypeEnum, JobStatusEnum

def utc_now():
    return datetime.now(timezone.utc)

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True,autoincrement=True, index=True)
    title = Column(String(255), nullable=False)
    job_type = Column(SQLEnum(JobTypeEnum), nullable=False)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(JobStatusEnum), nullable=False, default=JobStatusEnum.draft)
    funded_by = Column(String(255), nullable=True)
    visa_type= Column(String(255), nullable=True)
    job_tenure= Column(String(255), nullable=True)
    required_qualifications = Column(Text, nullable=True)
    preferred_qualifications = Column(Text, nullable=True)
    order = Column(Integer, nullable=False, default=1, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    
