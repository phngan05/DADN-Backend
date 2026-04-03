from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

class Settings(BaseSettings):
    # Supabase
    DATABASE_URL: str
    DATABASE_KEY: str
    DATABASE_SERVICE_ROLE_KEY: str
    DATABASE_JWT_SECRET: str
    
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

