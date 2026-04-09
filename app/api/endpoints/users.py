from fastapi import APIRouter, HTTPException, Depends
from app.core.database import supabase_client
from app.core.security import get_current_user_id
from app.schemas.user import User

router = APIRouter()

# Get user name and full name
@router.get("")
def get_profile(user_id: str = Depends(get_current_user_id)):
    try:
        response = supabase_client.table("USER")\
            .select("user_id, full_name, username, photo_url")\
            .eq('user_id', user_id)\
            .execute()
        return response.data[0]
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# Update user profile
@router.put("")
def update_profile(user: User, user_id: str = Depends(get_current_user_id)):
    try:
        update_data = {
            "full_name": user.full_name,
            "username": user.username,
            "photo_url": user.photo_url
        }
        response = supabase_client.table("USER")\
            .update(update_data)\
            .eq('user_id', user_id)\
            .execute()
        return response.data
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
