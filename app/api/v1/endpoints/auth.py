from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.services.auth import (
    verify_password,
    create_access_token,
    get_current_user,
    get_current_active_user,
    get_current_admin
)
from app.core.config import settings
from app.schemas.auth import Token

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.primary_email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_deleted == True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your account has been deleted by the system administrator. If you believe this is a mistake or have any concerns, please reach out to our support team for assistance."
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.primary_email}, expires_delta=access_token_expires
    )
    
    return {
        "role": user.role,
        "user_id": user.id,
        "name": f"{user.first_name} {user.last_name}",
        "access_token": access_token,
        "token_type": "bearer"
    }

