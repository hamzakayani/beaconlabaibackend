
from sqlalchemy import ARRAY, JSON, Column, Integer, String, DateTime, Boolean, Text,Index
from app.db.database import Base
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(Text, nullable=False, default="")
    abstract = Column(Text, nullable=True, default="")
    authers = Column(Text, default="")
    journal = Column(Text,default="")
    publish_date = Column(String(250), default="", index=True)
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

    @classmethod
    def search_by_tags(cls, search_tags):
        #search_tags = [tag.lower() for tag in search_tags]
        return cls.query.filter(
            cls.tags['tag'].astext.cast(ARRAY(String)).contains(search_tags)
        )