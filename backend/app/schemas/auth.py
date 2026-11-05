"""
Authentication-related Pydantic schemas for Whicoustic API.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, validator
from typing import Optional, List
from datetime import datetime, date

class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    dob: date

    @field_validator('dob')
    @classmethod
    def validate_dob(cls, v: date) -> date:
        """Validate that user is at least 17 years old in compliance with digital biometric licensing regulations."""
        today = date.today()
        # Compute exact calendar age and fractional days
        calendar_age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        age = max(calendar_age, (today - v).days / 365.2425)
        if age < 17:
            raise ValueError(
                "Users must be at least 17 years old to register on Whicoustic in compliance with digital biometric licensing regulations."
            )
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter') 
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)

class UserResponse(BaseModel):
    """Schema for user information response."""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    dob: Optional[date] = None
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_premium: bool
    subscription_tier: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=1000)
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class ApiKeyCreate(BaseModel):
    """Schema for creating API key."""
    name: str = Field(..., min_length=1, max_length=255)
    scopes: List[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = Field(None, gt=0, le=365)

class ApiKeyResponse(BaseModel):
    """Schema for API key response."""
    key_id: str
    key: str  # Only returned once during creation
    name: str
    key_prefix: str  # First few characters for display
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True