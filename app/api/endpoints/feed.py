from fastapi import APIRouter, HTTPException, Depends
from app.core.database import supabase_client
from app.core.security import get_current_user_id
from app.schemas.adafruit import FeedCreate, Feed, FeedUpdate 

router = APIRouter()



@router.get("")
def get_feeds(feed_id: str = None, user_id: str = Depends(get_current_user_id)):
    try:
        query = supabase_client.table("FEED")\
        .select("feed_id, feed_key, category, ADAFRUIT_SERVER(server_id, username)")
        
        
        if feed_id is not None:
            query = query.eq("feed_id", feed_id)
        else:
            query = query.eq("ADAFRUIT_SERVER.user_id", user_id)
            
        response = query.execute()
        
        return response.data
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
  
@router.put("")
def update_feed(feed: FeedUpdate):
    try:
        # Check if the feed exists
        existing_feed = supabase_client.table("FEED").select("*").eq("feed_id", feed.feed_id).execute()
        if not existing_feed.data:
            raise HTTPException(status_code=404, detail="Feed not found")

        # Update the feed
        response = supabase_client.table("FEED").update({
            "feed_key": feed.feed_key,
            "category": feed.category
        }).eq("feed_id", feed.feed_id).execute()

        return response.data[0]
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))   
    
@router.post("")
def create_feed(feed: FeedCreate, user_id: str = Depends(get_current_user_id)):
    try:
        print(f"DEBUG: Received feed data: {feed}")
        if not feed.feed_key or not feed.category:
            raise HTTPException(status_code=400, detail="feed_key and category are required")
        
        if feed.category not in ["Temperature", "Humidity", "Illuminance", "LED Intensity", "Fan Speed", "LED Status", "Servo"]:
            raise HTTPException(status_code=400, detail="Invalid category")
        
        response = supabase_client.table("ADAFRUIT_SERVER").select("server_id").eq("user_id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="User has no Adafruit information")
        server_id = response.data[0]["server_id"]
        feed_data = {
            "feed_key": feed.feed_key,
            "category": feed.category,
            "server_id": server_id
        }
                
        response = supabase_client.table("FEED").insert(feed_data).execute()
        
        return response.data[0]
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{feed_id}")
def delete_feed(feed_id: str):
    try:
        # Check if the feed exists
        existing_feed = supabase_client.table("FEED").select("*").eq("feed_id", feed_id).execute()
        if not existing_feed.data:
            raise HTTPException(status_code=404, detail="Feed not found")

        # Delete the feed
        response = supabase_client.table("FEED").delete().eq("feed_id", feed_id).execute()

        return {"status": "success", "message": "Feed deleted successfully"}
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))