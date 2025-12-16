import uuid
from sqlalchemy import ARRAY, JSON, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Index
from app.db.database import Base
from datetime import datetime, timezone
from app.schemas.screening_enum import UploadSourceEnum, DecisionEnum, PaperIdTypeEnum, UploadTypeEnum, ScreeningDecision

def utc_now():
    return datetime.now(timezone.utc)

class UploadTypeEnum(str, Enum):
    CSV = "csv"
    XML = "xml"
    PUBMED = "pubmed"
    DOI = "doi"
    MANUAL = "manual"
    NO = "none"

class Papers(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False, default="")
    abstract = Column(Text, nullable=True, default="")
    authers = Column(Text, default="")
    journal = Column(Text,default="")
    publish_date = Column(String(250), default="", index=True)
    upload_type = Column(Enum(UploadTypeEnum), default=UploadTypeEnum.NO)
    pubmed_id = Column(String(100), default="", index=True)
    nct_number = Column(String(50), default="",index=True)
    tags = Column(JSON, default = lambda: {"tag": []})
    doi = Column(String(100), default="", index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)


    __table_args__ = (
        Index('ix_papers_title', 'title', mysql_length=191),
        Index('ix_papers_abstract', 'abstract', mysql_length=191),
        Index('ix_papers_authers', 'authers', mysql_length=191),
    )