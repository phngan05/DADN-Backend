from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base schema cho User"""
    full_name: str = Field(None, description = "Full name")
    username: str = Field(None, description = "User name")
    
    class Config:
        from_attributes = True 

class UserCreate(UserBase):
    """Schema for creating new user"""
    password: str = Field(..., min_length=8, description="Password")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must have at least 8 characters!')
        return v

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    full_name: str = None
    username: str = None
    password: str = Field(None, min_length=8)
    
    class Config:
        from_attributes = True

class User(UserBase):
    """Schema for getting user information"""
    id: str = Field(..., description="User ID")
    created_at: Optional[datetime] = None