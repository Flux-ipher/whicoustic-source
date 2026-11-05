"""
User model for Whicoustic platform.
"""

from datetime import datetime
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Text, Date
from ..core.database import Base


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    firebase_uid = Column(String(128), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    dob = Column(Date, nullable=True)
    display_name = Column(String(255), nullable=True)
    avatar = Column(String(512), nullable=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    role = Column(String(50), default="user")
    location = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    subscription_tier = Column(String(50), default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.email})>"

