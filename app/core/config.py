from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str #= "sqlite:///./sql_app.db"
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    PAGINATION_SIZE: int = 10
    # CONTACT_EMAIL: str = "riaz.irbaz@mayo.edu"
    CONTACT_EMAIL: str = "habzayasin238@gmail.com"
    CONTACT_ADDRESS: str = "Johnson Medical Research Building, 13400, E shea Blvd, Scottsdale, Arizona, 85259"
    ADMIN_NOTIFICATION_EMAIL: str = ""  # Optional: Set in .env to receive email notifications
    
    IMAGES_UPLOAD_DIR: Path = Path("images")
    IMAGE_MAX_FILE_SIZE:int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_IMAGE_EXTENSIONS:set = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    
    # CV Upload Settings
    CV_UPLOAD_DIR: Path = Path("cv_uploads")
    CV_MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_CV_EXTENSIONS: set = {".pdf", ".doc", ".docx"}


    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()