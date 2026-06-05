from pathlib import Path

from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH, override=True)

class Settings(BaseSettings):
    # Supabase
    DATABASE_URL: str
    DATABASE_KEY: str
    DATABASE_SERVICE_ROLE_KEY: str
    DATABASE_JWT_SECRET: str

    # Face++
    FACEPP_API_KEY: str
    FACEPP_API_SECRET: str
    
    # Application
    PROJECT_NAME: str = "ComHome API" 
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API
    API_V1_STR: str = "/api"  
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

