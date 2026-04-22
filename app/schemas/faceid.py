from pydantic import BaseModel, Field, validator

class FaceIDUpdate(BaseModel):
    """Schema for updating feed information"""
    id : str = Field(..., description="FaceID ID")
    is_active: bool = Field(None, description = "Is active")
    
    class Config:
        from_attributes = True