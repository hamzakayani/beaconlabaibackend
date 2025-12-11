from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    role: Optional[str] = None
    user_id: Optional[int] = None
    name: Optional[str] = None
