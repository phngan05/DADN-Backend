from fastapi import APIRouter, HTTPException, Depends
from app.core.database import supabase_client
from app.core.security import get_current_user_id
from app.schemas.user import NotiCreate
router = APIRouter()

# Get notification for user
@router.get("/")
def get_noti(user_id: str = Depends(get_current_user_id)):
    try:
        response = supabase_client.table("NOTIFICATION")\
            .select("*")\
            .eq('user_id', user_id)\
            .execute()
        return response.data
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# Update notification as read
@router.patch("/")
def update_noti_read(user_id: str = Depends(get_current_user_id)):
    try:
        update_data = {
            "is_read": True
        }
        response = supabase_client.table("NOTIFICATION")\
            .update(update_data)\
            .eq('user_id', user_id)\
            .execute()
        return response.data
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Create new notification
@router.post("/")
def create_noti(noti: NotiCreate, user_id: str = Depends(get_current_user_id)):
    try:
        new_noti = {
            "user_id": user_id,
            "title": noti.title,
            "body": noti.body,
            "is_read": noti.is_read
        }
        response = supabase_client.table("NOTIFICATION")\
            .insert(new_noti)\
            .execute()
        return response.data
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))