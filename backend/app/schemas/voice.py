"""
Voice-related Pydantic schemas for Whicoustic API.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class VoiceCreate(BaseModel):
    """Schema for voice creation."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class VoiceUpdate(BaseModel):
    """Schema for voice updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class VoiceUploadResponse(BaseModel):
    """Schema for voice upload response."""
    voice_id: str
    name: str
    status: str
    duration: float
    quality_score: float
    upload_time: datetime
    next_steps: str
    
    class Config:
        from_attributes = True

class VoiceResponse(BaseModel):
    """Schema for voice information response."""
    id: str
    name: str
    description: Optional[str] = None
    status: str
    duration: float
    quality_score: Optional[float] = None
    sample_rate: Optional[int] = None
    file_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True