from fastapi import APIRouter, HTTPException, Depends
from app.core.adafruit import active_adafruit_sessions
from app.core.security import get_current_user_id
from app.schemas.record import RecordUpdate
router = APIRouter()

def get_user_mqtt(user_id: str = Depends(get_current_user_id)):
    if user_id not in active_adafruit_sessions:
        raise HTTPException(status_code=404, detail="Adafruit session not active. Please login again.")
    return active_adafruit_sessions[user_id]

@router.get("/all")
def get_all_feeds(mqtt_service = Depends(get_user_mqtt)):
    """Get all feed data for the user"""
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