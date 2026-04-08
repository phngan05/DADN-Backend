from fastapi import APIRouter, HTTPException, Depends
from app.core.adafruit import active_adafruit_sessions
from app.core.security import get_current_user_id
from app.schemas.record import RecordUpdate
from app.core.adafruit import AdafruitMQTT, active_adafruit_sessions
from app.core.database import supabase_client
import asyncio

router = APIRouter()

def get_user_mqtt(user_id: str = Depends(get_current_user_id)):
    if user_id not in active_adafruit_sessions:
        raise HTTPException(status_code=404, detail="Adafruit session not active. Please login again.")
    return active_adafruit_sessions[user_id]

async def get_or_create_mqtt_service(user_id: str):
    if user_id not in active_adafruit_sessions:
        ada_res = supabase_client.table("ADAFRUIT_SERVER").select("*").eq("user_id", user_id).execute()
        if not ada_res.data:
            raise HTTPException(status_code=404, detail="Adafruit config not found")
        
        config = ada_res.data[0]
        loop = asyncio.get_event_loop()
        new_service = AdafruitMQTT(config["username"], str(user_id), config["api_key"], loop=loop)
        new_service.start()
        active_adafruit_sessions[str(user_id)] = new_service
        await asyncio.sleep(1) 
        
    return active_adafruit_sessions[str(user_id)]

@router.get("/all")
async def get_all_feeds(user_id: str = Depends(get_current_user_id)):
    """API này vừa kích hoạt kết nối, vừa lấy dữ liệu hiện tại"""
    mqtt_service = await get_or_create_mqtt_service(user_id)
    return mqtt_service.feeds_data

@router.get("/history/{feed_key}")
def get_history(feed_key: str, mqtt_service = Depends(get_user_mqtt)):
    """Get historical data for a specific feed"""
    data = mqtt_service.get_feed_history(feed_key)
    return {"feed": feed_key, "history": data}

@router.put("/")
def update_value(record: RecordUpdate, mqtt_service = Depends(get_user_mqtt)):
    """Control device by updating feed value"""
    topic = f"{mqtt_service.username}/feeds/{record.feed_key}"
    mqtt_service.client.publish(topic, record.value)
    return {"status": "success", "feed": record.feed_key, "value": record.value}