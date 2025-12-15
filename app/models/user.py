from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum
from app.models.role import UserRole
from app.db.database import Base
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    primary_email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(250), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)