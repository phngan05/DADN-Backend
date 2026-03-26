# app/core/database.py
from supabase import create_client, Client
from app.core.config import settings

supabase_client: Client = create_client(
    settings.DATABASE_URL, 
    settings.DATABASE_SERVICE_ROLE_KEY
)

