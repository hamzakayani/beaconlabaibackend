from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.user import User
from app.models.role import UserRole
from app.services.auth import get_password_hash

def create_initial_admin():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin:
            admin = User(
                first_name="Admin",
                last_name="User",
                primary_email="admin@admin.com",
                hashed_password=get_password_hash("12345678"),
                role=UserRole.ADMIN
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

if __name__ == "__main__":
    create_initial_admin()

