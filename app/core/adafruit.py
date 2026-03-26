import paho.mqtt.client as mqtt
from app.core.config import settings

class AdafruitMQTT:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.username_pw_set(settings.ADAFRUIT_AIO_USERNAME, settings.ADAFRUIT_AIO_KEY)
        
        self.feeds_data = {}
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Adafruit MQTT Connected!")
            topic = f"{settings.ADAFRUIT_AIO_USERNAME}/feeds/+"
            client.subscribe(topic)
        else:
            print(f"❌ Connection failed: {rc}")

    def on_message(self, client, userdata, msg):
        # Lấy tên feed từ topic (ví dụ: 'username/feeds/led' -> 'led')
        feed_name = msg.topic.split('/')[-1]
        payload = msg.payload.decode()
        
        # Lưu vào dictionary
        self.feeds_data[feed_name] = payload
        print(f"📩 Update [{feed_name}]: {payload}")

    def start(self):
        self.client.connect("io.adafruit.com", 1883, 60)
        self.client.loop_start()

# Khởi tạo instance
adafruit_service = AdafruitMQTT()