from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class NotiBase(BaseModel):
    """Base schema cho Notification"""
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    noti_type: str = Field(..., description="Notification type")
    device_category: Optional[str] = None
    
    class Config:
        from_attributes = True 

class NotiCreate(NotiBase):
    """Schema for creating new notification"""
    pass