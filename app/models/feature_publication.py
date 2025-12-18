from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum, Text
from app.db.database import Base
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)


class FeaturePublication(Base):
    __tablename__ = "feature_publication"

    id=Column(Integer,autoincrement=True,primary_key=True,index=True)
    image_url=Column(String(255),nullable=True,default="")
    title = Column(Text, nullable=False, default="")
    abstract = Column(Text, nullable=True, default="")
    authers = Column(Text, default="")
    journal = Column(Text,default="")
    paper_id = Column(String(100), default="", index=True)
    publish_date = Column(String(250), default="", index=True)
    pubmed_id = Column(String(100), default="", index=True)
    nct_number = Column(String(50), default="",index=True)
    doi = Column(String(100), default="", index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)