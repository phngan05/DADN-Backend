from fastapi import APIRouter, HTTPException
from app.core.adafruit import adafruit_service

router = APIRouter()

@router.get("/led")
def get_led_status():
    """Get LED intensity"""
    val = adafruit_service.feeds_data.get("led")
    if val is None:
        return {"status": "unknown", "value": "0"}
    return {"status": "success", "value": val}

@router.get("/temperature")
def get_temperature():
    """Get temperature"""
    val = adafruit_service.feeds_data.get("temperature")
    if val is None:
        raise HTTPException(status_code=404, detail="Temperature data not ready")
    return {"sensor": "temperature", "value": float(val), "unit": "°C"}

@router.get("/all")
def get_all_feeds():
    """Get all"""
    return adafruit_service.feeds_data