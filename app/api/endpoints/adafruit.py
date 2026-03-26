from fastapi import APIRouter, HTTPException
from app.core.database import supabase_client
from app.core.security import get_password_hash
from app.schemas.user import UserCreate

router = APIRouter()

@router.get("/all-feeds")
def get_all_feeds():
    try:
        response = supabase_client.table("FEED")\
            .select("id, name, category, ADAFRUIT(user_id)")\
            .execute()
        
        return response.data
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    