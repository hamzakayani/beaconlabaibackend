from pydantic import BaseModel
from app.models.role import UserRole

class Token(BaseModel):
    access_token: str
    token_type: str
    role: UserRole
    user_id: int
    name: str

