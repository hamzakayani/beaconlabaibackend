from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime
from app.db.database import Base
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True,autoincrement=True, index=True)
    name = Column(String(50), nullable=False,default="")
    category = Column(String(50), nullable=False,default="")
    role = Column(String(50), nullable=False,default="")
    designation = Column(String(50), nullable=False,default="")
    description = Column(Text, nullable=False,default="")
    image_url = Column(String(255), nullable=False,default="")
    hyperlink = Column(String(255), nullable=False,default="")
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)



