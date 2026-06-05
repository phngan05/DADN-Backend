from fastapi import APIRouter, HTTPException, Depends
from app.core.security import get_current_user_id
from app.schemas.record import RecordUpdate
from app.core.adafruit import AdafruitMQTT, active_adafruit_sessions
from app.core.database import supabase_client
from app.api.endpoints.feed import get_feeds
import asyncio
import numpy as np
from app.models.models import MODEL
from app.core.websocket_manager import manager
router = APIRouter()


def get_user_mqtt(user_id: str = Depends(get_current_user_id)):
    if user_id not in active_adafruit_sessions:
        raise HTTPException(status_code=404, detail="Adafruit session not active. Please login again.")
    return active_adafruit_sessions[user_id]


async def get_or_create_mqtt_service(user_id: str):
    user_id = str(user_id)

    if user_id not in active_adafruit_sessions:
        ada_res = supabase_client.table("ADAFRUIT_SERVER").select("*").eq("user_id", user_id).execute()
        if not ada_res.data:
            raise HTTPException(status_code=404, detail="Adafruit config not found")

        config = ada_res.data[0]
        loop = asyncio.get_event_loop()
        new_service = AdafruitMQTT(config["username"], user_id, config["api_key"], loop=loop)
        new_service.start()
        active_adafruit_sessions[user_id] = new_service
        await asyncio.sleep(1)

    return active_adafruit_sessions[user_id]


@router.get("/all")
async def get_all_feeds(user_id: str = Depends(get_current_user_id)):
    """Get all latest MQTT feed values for the current user."""
    mqtt_service = await get_or_create_mqtt_service(user_id)
    return mqtt_service.feeds_data

@router.get("/auto/status")
async def get_auto_status(user_id: str = Depends(get_current_user_id)):
    """Return backend source-of-truth for Automatic/Manual mode."""
    mqtt_service = await get_or_create_mqtt_service(user_id)
    return {"auto_mode": bool(mqtt_service.auto_mode)}


@router.get("/history/{feed_key}")
def get_history(feed_key: str, mqtt_service=Depends(get_user_mqtt)):
    """Get historical data for a specific feed."""
    data = mqtt_service.get_feed_history(feed_key)
    return {"feed": feed_key, "history": data}


def publish_value(record: RecordUpdate, mqtt_service: AdafruitMQTT):
    """
    Shared logic for publishing a value to Adafruit.

    IMPORTANT: This function intentionally does not use Depends(...), so it can be
    called safely from routes, MQTT callbacks, and auto mode logic.
    """
    if not record.feed_key:
        raise HTTPException(status_code=400, detail="feed_key is required")

    topic = f"{mqtt_service.username}/feeds/{record.feed_key}"
    mqtt_service.client.publish(topic, int(record.value))
    value = int(record.value)


    # Update local cache immediately so the API/UI can see the new control value
    # without waiting for Adafruit to echo the MQTT message back.
    mqtt_service.feeds_data[record.feed_key] = str(int(record.value))
    try:
        asyncio.run_coroutine_threadsafe(
            manager.send_personal_message(
                {"feed": record.feed_key, "value": value},
                mqtt_service.user_id,
            ),
            mqtt_service.loop,
        )
    except Exception as e:
        print(f"⚠️ WebSocket notify failed for {record.feed_key}: {e}")

    return {"status": "success", "feed": record.feed_key, "value": int(record.value)}


@router.put("")
def update_value(record: RecordUpdate, mqtt_service=Depends(get_user_mqtt)):
    """Control device by updating feed value."""
    return publish_value(record=record, mqtt_service=mqtt_service)


def _category_to_feed_key(feed_info):
    return {f.get("category"): f.get("feed_key") for f in feed_info or []}


def _get_float_feed(mqtt_service: AdafruitMQTT, feed_key: str, category: str):
    if not feed_key:
        raise ValueError(f"Missing feed_key for category: {category}")

    raw_value = mqtt_service.feeds_data.get(feed_key)
    if raw_value is None:
        raise ValueError(f"Missing MQTT value for {category} feed: {feed_key}")

    return float(raw_value)


def run_auto_update(feed_info, mqtt_service: AdafruitMQTT):
    """
    Shared auto-control logic.

    This function intentionally does not use FastAPI Depends(...). It is safe to
    call from the /auto route and from the MQTT on_message callback.
    """
    if not mqtt_service.auto_mode:
        return {
            "status": "skipped",
            "auto_mode": False,
            "message": "Auto mode is disabled",
        }

    if mqtt_service.is_auto_updating:
        return {
            "status": "skipped",
            "auto_mode": True,
            "message": "Auto update is already running",
        }

    mqtt_service.is_auto_updating = True
    try:
        feeds = _category_to_feed_key(feed_info)

        temp_feed = feeds.get("Temperature")
        humid_feed = feeds.get("Humidity")
        fan_feed = feeds.get("Fan Speed")

        light_feed = feeds.get("Illuminance")
        led_feed = feeds.get("LED Intensity")
        missing_categories = [
            category
            for category, feed_key in {
                "Temperature": temp_feed,
                "Humidity": humid_feed,
                "Fan Speed": fan_feed,
                "Illuminance": light_feed,
                "LED Intensity": led_feed,
            }.items()
            if not feed_key
        ]
        if missing_categories:
            return {
                "status": "error",
                "message": "Missing feed configuration",
                "missing_categories": missing_categories,
                "feeds": feeds,
            }

        temperature = _get_float_feed(mqtt_service, temp_feed, "Temperature")
        humidity = _get_float_feed(mqtt_service, humid_feed, "Humidity")
        light = _get_float_feed(mqtt_service, light_feed, "Illuminance")


        input_data = np.array([[temperature, humidity]])

        prediction = MODEL.predict(input_data)[0]
        speed_output = int(np.round(prediction))

        if speed_output < 60:
            speed_output = 0
        elif speed_output > 100:
            speed_output = 100

        light_data = int(light)
        if light_data < 30:
            led_output = int(np.random.randint(85, 100))
        elif light_data < 50:
            led_output = int(np.random.randint(65, 89))
        elif light_data < 70:
            led_output = int(np.random.randint(50, 71))
        elif light_data < 85:
            led_output = int(np.random.randint(30, 55))
        else:
            led_output = int(np.random.randint(0, 32))
        
        speed_res = publish_value(
            record=RecordUpdate(feed_key=fan_feed, value=speed_output),
            mqtt_service=mqtt_service,
        )

        led_res = publish_value(
            record=RecordUpdate(feed_key=led_feed, value=led_output),
            mqtt_service=mqtt_service,
        )

        return {
            "status": "success",
            "auto_mode": True,
            "inputs": {
                "temperature": temperature,
                "humidity": humidity,
                "illuminance": light,
            },
            "fan": speed_res,
            "led": led_res,
        }

    except Exception as e:
        print(f"❌ Auto update error: {e}")
        return {
            "status": "error",
            "auto_mode": True,
            "message": str(e),
        }
    finally:
        mqtt_service.is_auto_updating = False


@router.put("/auto")
def auto_update(
    enabled: bool = True,
    feed_info=Depends(get_feeds),
    mqtt_service=Depends(get_user_mqtt),
):
    """Enable/disable auto mode and run one immediate auto update when enabled."""
    mqtt_service.auto_mode = enabled

    # Keep the MQTT service feed mapping fresh in case the user changed feeds
    # after the MQTT session was created.
    mqtt_service.feed_info = feed_info

    if not enabled:
        return {
            "status": "success",
            "auto_mode": False,
            "message": "Auto mode disabled",
        }

    result = run_auto_update(feed_info=feed_info, mqtt_service=mqtt_service)
    return {
        "status": "success" if result.get("status") != "error" else "error",
        "auto_mode": True,
        "message": "Auto mode enabled",
        "result": result,
    }
