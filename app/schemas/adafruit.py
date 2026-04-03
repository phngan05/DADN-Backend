from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class AdafruitBase(BaseModel):
    """Base schema cho Adafruit"""
    user_name: str = Field(None, description = "User name")
    
    class Config:
        from_attributes = True 



class Adafruit(AdafruitBase):
    """Schema for getting Adafruit information"""
    id: str = Field(..., description="Adafruit ID")
    created_at: Optional[datetime] = None
    
class AdafruitCreate(AdafruitBase):
    """Schema for creating new Adafruit information"""
    user_id: str = Field(None, description = "User ID")
    api_key: str = Field(None, description = "API key")


class FeedBase(BaseModel):
    """Base schema cho Feed"""
    feed_key: str = Field(None, description = "Feed key")
    category: str = Field(None, description = "Feed category")
    
    class Config:
        from_attributes = True
        
class Feed(FeedBase):
    """Schema for getting Feed information"""
    feed_id: str = Field(..., description="Feed ID")
    created_at: Optional[datetime] = None
    server_id: str = Field(None, description = "Server ID")
    

class FeedCreate(FeedBase):
    """Schema for creating new feed"""
    pass

class FeedUpdate(BaseModel):
    """Schema for updating feed information"""
    feed_key: str = None
    category: str = None
    
    class Config:
        from_attributes = True