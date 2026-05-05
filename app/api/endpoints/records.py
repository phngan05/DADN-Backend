from fastapi import APIRouter, HTTPException, Depends
from app.core.security import get_current_user_id
from app.schemas.record import RecordUpdate, AutoUpdate
from app.core.adafruit import AdafruitMQTT, active_adafruit_sessions
from app.core.database import supabase_client
from app.api.endpoints.feed import get_feeds
import asyncio
import numpy as np
from app.models.models import MODEL

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
    """Get all feeds for the current user"""
    mqtt_service = await get_or_create_mqtt_service(user_id)
    return mqtt_service.feeds_data

@router.get("/history/{feed_key}")
def get_history(feed_key: str, mqtt_service = Depends(get_user_mqtt)):
    """Get historical data for a specific feed"""
    data = mqtt_service.get_feed_history(feed_key)
    return {"feed": feed_key, "history": data}

@router.put("")
def update_value(record: RecordUpdate, mqtt_service = Depends(get_user_mqtt)):
    """Control device by updating feed value"""
    topic = f"{mqtt_service.username}/feeds/{record.feed_key}"
    mqtt_service.client.publish(topic, record.value)
    return {"status": "success", "feed": record.feed_key, "value": record.value}

@router.put("/auto")
def auto_update(feed_info = Depends(get_feeds), mqtt_service = Depends(get_user_mqtt)):
    
    feeds = {f['category']: f['feed_key'] for f in feed_info}
    
    # Get feed for fan speed 
    temp_feed  = feeds.get("Temperature")
    humid_feed = feeds.get("Humidity")
    fan_feed   = feeds.get("Fan Speed")
    
    # Get feed for led
    light_feed = feeds.get("Illuminance")
    led_feed   = feeds.get("LED Intensity")
    
    # Get temperature and humidity
    temperature = mqtt_service.feeds_data[temp_feed]
    humidity = mqtt_service.feeds_data[humid_feed]
    
    # Get light
    light = mqtt_service.feeds_data[light_feed]
    
    # Set 2 dimesion array
    input_data = np.array([[temperature, humidity]])
    light_data = int(light)
    
    # Make prediction
    prediction = MODEL.predict(input_data)[0]
    speed_output = int(np.round(prediction))
    
    if speed_output < 60:
        speed_output = 0
    elif speed_output > 100:
        speed_output = 100
    
    # Light prediction simulation
    led_output = 0
    if light_data < 30:
        led_output = np.random.randint(85, 100, 1)[0]
    elif light_data < 50:
        led_output = np.random.randint(65, 89, 1)[0]
    elif light_data < 70:
        led_output = np.random.randint(50, 71, 1)[0]
    elif light_data < 85:
        led_output = np.random.randint(30, 55, 1)[0]
    else:
        led_output = np.random.randint(0, 32, 1)[0]
        
    speed_to_update = RecordUpdate(feed_key=fan_feed, value=speed_output)
    led_to_update = RecordUpdate(feed_key=led_feed, value=led_output)
    
    speed_res = update_value(record=speed_to_update, mqtt_service=mqtt_service)
    led_res = update_value(record=led_to_update, mqtt_service=mqtt_service)
    
    return speed_res, led_res, led_state_res