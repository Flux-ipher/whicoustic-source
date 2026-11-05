"""
Text-to-Speech related Pydantic schemas for Whicoustic API.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime

class VoiceParams(BaseModel):
    """Schema for voice synthesis parameters."""
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-1.0, le=1.0)
    emotion: str = Field(default="neutral", pattern=r"^(neutral|happy|sad|angry|excited|calm)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "speed": 1.0,
                "pitch": 0.0,
                "emotion": "neutral"
            }
        }

class SynthesizeRequest(BaseModel):
    """Schema for TTS synthesis request."""
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str = Field(..., pattern=r"^voice_[a-zA-Z0-9]+$")
    license_token: Optional[str] = Field(None, description="License token for commercial use")
    voice_params: Optional[VoiceParams] = None
    output_format: str = Field(default="wav", pattern=r"^(wav|mp3|ogg)$")
    
    @validator('text')
    def validate_text(cls, v):
        """Validate text content."""
        # Remove excessive whitespace
        v = ' '.join(v.split())
        if not v.strip():
            raise ValueError('Text cannot be empty or only whitespace')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, this is a test of voice synthesis.",
                "voice_id": "voice_abc123",
                "license_token": "lic_token_xyz789",
                "voice_params": {
                    "speed": 1.0,
                    "pitch": 0.0,
                    "emotion": "neutral"
                },
                "output_format": "wav"
            }
        }

class SynthesizeResponse(BaseModel):
    """Schema for TTS synthesis response."""
    job_id: str
    audio_url: str
    watermark_id: str
    license_id: Optional[str] = None
    status: str
    created_at: datetime
    estimated_duration: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "tts_abc123def456",
                "audio_url": "/api/v1/tts/download/tts_abc123def456",
                "watermark_id": "wm_xyz789abc123",
                "license_id": "lic_commercial_001",
                "status": "completed",
                "created_at": "2023-12-01T12:00:00Z"
            }
        }

class TTSJobResponse(BaseModel):
    """Schema for TTS job status response."""
    job_id: str
    status: str = Field(..., pattern=r"^(pending|processing|completed|failed|cancelled)$")
    progress: int = Field(..., ge=0, le=100)
    audio_url: Optional[str] = None
    watermark_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "job_id": "tts_abc123def456",
                "status": "completed",
                "progress": 100,
                "audio_url": "/api/v1/tts/download/tts_abc123def456",
                "watermark_id": "wm_xyz789abc123",
                "created_at": "2023-12-01T12:00:00Z",
                "completed_at": "2023-12-01T12:00:05Z",
                "processing_time_ms": 5000
            }
        }

class BatchSynthesizeRequest(BaseModel):
    """Schema for batch TTS synthesis request."""
    requests: list[SynthesizeRequest] = Field(..., min_items=1, max_items=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "requests": [
                    {
                        "text": "First text to synthesize",
                        "voice_id": "voice_abc123"
                    },
                    {
                        "text": "Second text to synthesize", 
                        "voice_id": "voice_def456"
                    }
                ]
            }
        }

class BatchSynthesizeResponse(BaseModel):
    """Schema for batch TTS synthesis response."""
    batch_id: str
    job_ids: list[str]
    total_requests: int
    message: str
    status_endpoint: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_abc123def456",
                "job_ids": ["tts_job1", "tts_job2"],
                "total_requests": 2,
                "message": "Batch synthesis started successfully",
                "status_endpoint": "/api/v1/tts/jobs/{job_id}"
            }
        }

class TTSRequest(BaseModel):
    """Schema for basic TTS request."""
    text: str = Field(..., min_length=1, max_length=5000)
    voice_model_id: str = Field(..., description="ID of the voice model to use")
    output_format: str = Field(default="wav", pattern=r"^(wav|mp3|ogg)$")
    voice_settings: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, this is a test message.",
                "voice_model_id": "model_abc123",
                "output_format": "wav"
            }
        }

class TTSResponse(BaseModel):
    """Schema for TTS response."""
    job_id: str
    estimated_duration: float
    estimated_cost: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_abc123",
                "estimated_duration": 10.5,
                "estimated_cost": 0.25
            }
        }

class TTSResultResponse(BaseModel):
    """Schema for TTS job result response."""
    job_id: str
    output_file: str
    audio_url: str
    watermark_id: Optional[str] = None
    license_id: Optional[str] = None
    duration: float
    quality_score: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_abc123",
                "output_file": "/data/audio/job_abc123.wav",
                "audio_url": "/api/v1/tts/job/job_abc123/download",
                "watermark_id": "wm_xyz789",
                "duration": 10.5,
                "quality_score": 0.95
            }
        }
