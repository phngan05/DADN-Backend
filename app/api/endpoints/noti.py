from fastapi import APIRouter, HTTPException, Depends, Request
from app.core.database import supabase_client
from app.core.security import get_current_user_id
from app.schemas.noti import NotiCreate
import json
import asyncio
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

# Get notification for user
@router.get("/{user_id}")
async def stream_notifications(request: Request, user_id: str):
    async def event_generator():
        initial_data = supabase_client.table("NOTIFICATION")\
            .select("*")\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        
        yield {
            "event": "message",
            "data": json.dumps(initial_data.data)
        }

        last_count = len(initial_data.data)
        
        try:
            while True:
                if await request.is_disconnected():
                    break

                current_response = supabase_client.table("NOTIFICATION")\
                    .select("*")\
                    .eq('user_id', user_id)\
                    .order('created_at', desc=True)\
                    .execute()
                
                if len(current_response.data) != last_count:
                    last_count = len(current_response.data)
                    yield {
                        "event": "message",
                        "data": json.dumps(current_response.data)
                    }
                
                await asyncio.sleep(5) 
        except Exception as e:
            print(f"Error in SSE stream: {e}")

    return EventSourceResponse(event_generator())

# Update notification as read
@router.patch("")
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
@router.post("")
def create_noti(noti: NotiCreate, user_id: str = Depends(get_current_user_id)):
    try:
        new_noti = {
            "user_id": user_id,
            "title": noti.title,
            "body": noti.body,
            "noti_type": noti.noti_type,
            "device_category": noti.device_category,
        }
        response = supabase_client.table("NOTIFICATION")\
            .insert(new_noti)\
            .execute()
        return response.data
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper function to create notification with explicit user_id (for internal use)
def create_notification(noti: NotiCreate, user_id: str):
    """Create notification with explicit user_id - for internal use"""
    try:
        new_noti = {
            "user_id": user_id,
            "title": noti.title,
            "body": noti.body,
            "noti_type": noti.noti_type,
            "device_category": noti.device_category,
        }
        response = supabase_client.table("NOTIFICATION")\
            .insert(new_noti)\
            .execute()
        return response.data
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return None