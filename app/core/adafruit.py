import asyncio
from .websocket_manager import manager
import paho.mqtt.client as mqtt
from Adafruit_IO import Client
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