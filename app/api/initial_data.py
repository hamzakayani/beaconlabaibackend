from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.user import User
from app.models.role import UserRole
from app.services.auth import get_password_hash
import secrets

def create_initial_admin():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin:
            # Generate a unique verification code for admin
            verification_code = secrets.token_urlsafe(32)
            
            admin = User(
                first_name="Admin",
                last_name="User",
                primary_email="admin@admin.com",
                hashed_password=get_password_hash("12345678"),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                verified_status=True,
                verification_code=verification_code
            )
            db.add(admin)
            db.commit()
            print("Admin user created successfully")
        else:
            print("Admin user already exists")
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
    finally:
        db.close()

