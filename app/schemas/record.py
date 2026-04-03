from pydantic import BaseModel

class RecordUpdate(BaseModel):
    feed_key: str
    value: str