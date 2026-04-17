from pydantic import BaseModel

class RecordUpdate(BaseModel):
    feed_key: str
    value: int
    
class AutoUpdate(BaseModel):
    temperature_feed: str
    humidity_feed: str
    fan_feed: str