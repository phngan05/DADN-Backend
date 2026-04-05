from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class NotiBase(BaseModel):
    """Base schema cho Notification"""
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    is_read: bool = Field(False, description="Whether notification is read")

    class Config:
        from_attributes = True 

class NotiCreate(NotiBase):
    """Schema for creating new notification"""
    user_id: str = Field(..., description="User ID")
