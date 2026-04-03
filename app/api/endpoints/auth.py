from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, APIRouter, HTTPException
from app.core.database import supabase_client
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.user import UserCreate
from app.core.adafruit import AdafruitMQTT, active_adafruit_sessions
import asyncio
router = APIRouter()

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Check user
    res = supabase_client.table("USER").select("*").eq("username", form_data.username).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="User not found")
    
    user = res.data[0]
    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Wrong password")

    # Get Adafruit info
    ada_res = supabase_client.table("ADAFRUIT_SERVER").select("*").eq("user_id", user["user_id"]).execute()
    if ada_res.data:
        config = ada_res.data[0]
        user_id_str = str(user["user_id"])
        
        # Initiate MQTT
        if user_id_str not in active_adafruit_sessions:
            loop = asyncio.get_event_loop()
            new_service = AdafruitMQTT(config["username"], user_id_str, config["api_key"], loop=loop)
            new_service.start()
            active_adafruit_sessions[user_id_str] = new_service

    # Create token
    token = create_access_token(data={"sub": str(user["user_id"])})
    return {"access_token": token, "token_type": "bearer", "user_id": user["user_id"]}

@router.post("/register")
def register_user(user_in: UserCreate):
    # Encoding password
    hashed_password = get_password_hash(user_in.password)
    
    # Data
    user_data = {
        "full_name": user_in.full_name,
        "username": user_in.username,
        "password": hashed_password,
    }
    
    
    try:
        # Insert data
        user_response = supabase_client.table("USER").insert(user_data).execute()
        adafruit_data = {
            "username": user_in.adafruit_username,
            "api_key": user_in.adafruit_api_key,
            "user_id": user_response.data[0]["user_id"]
        }
        adafruit_response = supabase_client.table("ADAFRUIT_SERVER").insert(adafruit_data).execute()
        
        # Return data
        if user_response.data and adafruit_response.data:
            return {"message": "User created successfully", "user": user_response.data[0], "adafruit": adafruit_response.data[0]}
            
    except Exception as e:
        print(f"SUPABASE ERROR: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"Lỗi: {str(e)}"
        )