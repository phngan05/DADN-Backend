from fastapi import APIRouter, HTTPException, Depends
from app.core.database import supabase_client
from app.core.security import get_current_user_id
from app.schemas.faceid import FaceIDUpdate

router = APIRouter()


@router.get("")
def get_faceids():
    try:
        print("get")
        query = supabase_client.table("FACEID")\
        .select("id, is_active, created_at", "USER(full_name, photo_url)")
      
        response = query.execute()
        flattened_data = [
        {
            "id": item["id"],
            "is_active": item["is_active"],
            "created_at": item["created_at"],
            "full_name": item["USER"]["full_name"] if item.get("USER") else None,
            "photo_url": item["USER"]["photo_url"] if item.get("USER") else None
        }
        for item in response.data
        ]
        return flattened_data
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Active/Inactive
@router.patch("")
def update_status(faceid: FaceIDUpdate):
    try:
        # Check if the faceid exists
        existing_feed = supabase_client.table("FACEID").select("*").eq("id", faceid.id).execute()
        if not existing_feed.data:
            raise HTTPException(status_code=404, detail="Feed not found")

        # Update the face
        response = supabase_client.table("FACEID").update({
            "is_active": faceid.is_active
        }).eq("id", faceid.id).execute()

        return response.data[0]
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))   
    
@router.post("")
def create_faceid(user_id: str = Depends(get_current_user_id)):
    try:
        
        faceid_data = {
            "user_id": user_id,
        }
                
        response = supabase_client.table("FACEID").insert(faceid_data).execute()
        
        return response.data[0]
        
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))