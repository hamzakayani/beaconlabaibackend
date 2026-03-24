from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime
from app.db.database import Base
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)

class LabGallery(Base):
    __tablename__ = "lab_gallery"
    
    id = Column(Integer, primary_key=True,autoincrement=True, index=True)
    title = Column(String(255), nullable=False,default="")
    content = Column(Text, nullable=False,default="")
    image_url = Column(String(255), nullable=True,default="")
    order = Column(Integer, nullable=False, default=1, index=True)
    category = Column(String(100), nullable=False, default="")
    date = Column(String(100), nullable=False, default="")
    location = Column(String(255), nullable=False, default="")
    participant = Column(String(100), nullable=False, default="")
    status = Column(String(50), nullable=False, default="")
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
