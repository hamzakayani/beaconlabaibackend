from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, Enum as SQLEnum
from app.db.database import Base
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc)

class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True,autoincrement=True, index=True)
    title = Column(String(255), nullable=False,default="")
    content = Column(Text, nullable=False,default="")
    image_url = Column(String(255), nullable=True,default="")
    hyperlink = Column(String(255), nullable=True,default="")
    publish_date = Column(DateTime, default=utc_now, nullable=False)
    order = Column(Integer, nullable=False, default=1, index=True)
    is_open = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

