import asyncio
from .websocket_manager import manager
import paho.mqtt.client as mqtt
from Adafruit_IO import Client
from app.api.endpoints.feed import get_feeds
from app.api.endpoints.noti import create_notification
from app.schemas.noti import NotiCreate
import time


class AdafruitMQTT:
    def __init__(self, username: str, user_id: str, api_key: str, loop: asyncio.AbstractEventLoop):
        self.user_id = user_id
        self.username = username
        self.api_key = api_key
        self.loop = loop
        
        self.aio = Client(username, api_key)
        
        self.client = mqtt.Client(client_id=f"fastapi_{username}_{int(time.time())}")
        self.client.username_pw_set(username, api_key)
        
        self.feeds_data = {}
        self.feed_info = get_feeds(user_id=user_id)
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def get_feed_history(self, feed_key: str):
        """Lấy dữ liệu lịch sử từ Adafruit IO REST API"""
        try:
            data = self.aio.data(feed_key)
            return [{"value": d.value, "time": d.created_at} for d in data]
        except Exception as e:
            print(f"Error fetching history for {feed_key}: {e}")
            return []

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Adafruit MQTT Connected: {self.username}")
            client.subscribe(f"{self.username}/feeds/+")
        else:
            print(f"❌ Connection failed for {self.username}: {rc}")

    def on_message(self, client, userdata, msg):
        feed_name = msg.topic.split('/')[-1]
        payload = msg.payload.decode()
        self.feeds_data[feed_name] = payload
        
        print(f"📩 [{self.username}] Update [{feed_name}]: {payload}")
        
        feeds = {f['feed_key']: f['category'] for f in self.feed_info}
        
        
        # Check for alert conditions and create notifications    
        if feeds.get(feed_name) == "Temperature":
            temperature = float(payload)
            if temperature > 38 or temperature < 16:
                noti = NotiCreate(
                    title="Temperature Alert",
                    body=f"The current temperature is {temperature}°C, which exceed the safe threshold.",
                    noti_type="Device",
                    device_category="Temperature"
                )
                create_notification(noti, self.user_id)
        
        if feeds.get(feed_name) == "Humidity":
            humidity = float(payload)
            if humidity > 65 or humidity < 40:
                noti = NotiCreate(
                    title="Humidity Alert",
                    body=f"The current humidity is {humidity}%, which is outside the allowed range.",
                    noti_type="Device",
                    device_category="Humidity"
                )
                create_notification(noti, self.user_id)
            
        if feeds.get(feed_name) == "Illuminance":
            light = float(payload)
            if light > 90:
                noti = NotiCreate(
                    title="Light Intensity Alert",
                    body=f"The current illuminance is {light}%, The house is currently too bright.",
                    noti_type="Device",
                    device_category="Illuminance"
                )
                create_notification(noti, self.user_id)
        

        data_to_send = {"feed": feed_name, "value": payload}
        
        asyncio.run_coroutine_threadsafe(
            manager.send_personal_message(data_to_send, self.user_id), 
            self.loop
        )
        
    def start(self):
        self.client.connect("io.adafruit.com", 1883, 60)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

# Biến toàn cục quản lý các session theo user_id
active_adafruit_sessions = {}