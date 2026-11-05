"""
License-related Pydantic schemas for Whicoustic API.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class LicenseCreate(BaseModel):
    """Schema for license creation."""
    voice_id: str = Field(..., pattern=r"^voice_[a-zA-Z0-9]+$")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    license_type: str = Field(..., pattern=r"^(personal|commercial|enterprise|educational|non_profit|custom)$")
    price: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    duration_days: Optional[int] = Field(None, gt=0, le=3650)
    usage_limit: Optional[int] = Field(None, gt=0)
    territory: Optional[List[str]] = None
    allowed_use_cases: Optional[List[str]] = None
    restrictions: Optional[Dict[str, Any]] = None

class LicenseResponse(BaseModel):
    """Schema for license information response."""
    id: str
    voice_id: str
    name: str
    description: Optional[str] = None
    license_type: str
    price: Optional[Decimal] = None
    currency: str
    duration_days: Optional[int] = None
    usage_limit: Optional[int] = None
    territory: Optional[List[str]] = None
    allowed_use_cases: Optional[List[str]] = None
    restrictions: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LicenseTokenRequest(BaseModel):
    """Schema for license token generation request."""
    purchaser_email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    purchaser_name: Optional[str] = Field(None, max_length=255)
    purchase_amount: Optional[Decimal] = Field(None, ge=0)
    custom_terms: Optional[Dict[str, Any]] = None

class LicenseTokenResponse(BaseModel):
    """Schema for license token response."""
    token: str
    token_id: str
    license_id: str
    purchaser_email: str
    expires_at: Optional[datetime] = None
    usage_remaining: Optional[int] = None
    terms_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class LicenseUsageResponse(BaseModel):
    """Schema for license usage response."""
    id: str
    license_id: str
    token_id: Optional[str] = None
    user_id: str
    voice_id: str
    text_length: int
    audio_duration: Optional[float] = None
    watermark_id: Optional[str] = None
    used_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True