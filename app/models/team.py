from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime
from app.db.database import Base
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    role = Column(String(50), nullable=False)
    designation = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String(255), nullable=False)
    hyperlink = Column(String(255), nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)



