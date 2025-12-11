from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.database import Base

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"