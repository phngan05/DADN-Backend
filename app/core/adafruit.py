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
        self.auto_mode = False
        self.is_auto_updating = False
        
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
        feed_name = msg.topic.split("/")[-1]
        payload = msg.payload.decode()

        # 1. Cập nhật cache trước tiên
        # Auto mode sẽ đọc giá trị mới nhất từ self.feeds_data
        self.feeds_data[feed_name] = payload

        print(f"📩 [{self.username}] Update [{feed_name}]: {payload}")

        # 2. Map feed_key -> category
        feeds = {
            f.get("feed_key"): f.get("category")
            for f in self.feed_info or []
        }

        category = feeds.get(feed_name)

        # 3. Gửi WebSocket cho frontend ngay sau khi có dữ liệu mới
        # Để UI cập nhật nhanh, không đợi xử lý auto xong
        data_to_send = {
            "feed": feed_name,
            "value": payload,
        }

        try:
            asyncio.run_coroutine_threadsafe(
                manager.send_personal_message(data_to_send, self.user_id),
                self.loop,
            )
        except Exception as e:
            print(f"⚠️ WebSocket send failed: {e}")

        # 4. Check alert conditions and create notifications
        try:
            if category == "Temperature":
                temperature = float(payload)

                if temperature > 38 or temperature < 16:
                    noti = NotiCreate(
                        title="Temperature Alert",
                        body=f"The current temperature is {temperature}°C, which exceeds the safe threshold.",
                        noti_type="Device",
                        device_category="Temperature",
                    )
                    create_notification(noti, self.user_id)

            elif category == "Humidity":
                humidity = float(payload)

                if humidity > 65 or humidity < 40:
                    noti = NotiCreate(
                        title="Humidity Alert",
                        body=f"The current humidity is {humidity}%, which is outside the allowed range.",
                        noti_type="Device",
                        device_category="Humidity",
                    )
                    create_notification(noti, self.user_id)

            elif category == "Illuminance":
                light = float(payload)

                if light > 90:
                    noti = NotiCreate(
                        title="Light Intensity Alert",
                        body=f"The current illuminance is {light}%. The house is currently too bright.",
                        noti_type="Device",
                        device_category="Illuminance",
                    )
                    create_notification(noti, self.user_id)

        except ValueError:
            print(f"⚠️ Invalid sensor value for {feed_name}: {payload}")
        except Exception as e:
            print(f"❌ Notification error: {e}")

        # 5. Sau khi feeds_data đã cập nhật giá trị mới, mới chạy auto
        if self.auto_mode and category in ["Temperature", "Humidity", "Illuminance"]:
            try:
                from app.api.endpoints.records import run_auto_update

                result = run_auto_update(
                    feed_info=self.feed_info,
                    mqtt_service=self,
                )

                if result and result.get("status") == "error":
                    print(f"❌ Auto update error: {result.get('message')}")

            except Exception as e:
                print(f"❌ Auto update error: {e}")
        
    def start(self):
        self.client.connect("io.adafruit.com", 1883, 60)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

# Biến toàn cục quản lý các session theo user_id
active_adafruit_sessions = {}