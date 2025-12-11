from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str #= "sqlite:///./sql_app.db"
    #SECRET_KEY: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()