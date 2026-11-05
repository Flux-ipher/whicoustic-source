"""
Usage log and license usage models for Whicoustic platform.
"""

from datetime import datetime
import uuid
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey
from ..core.database import Base


class UsageLog(Base):
    """General synthesis usage log model."""
    __tablename__ = "usage_logs"

    id = Column(String(36), primary_key=True, default=lambda: f"usage_{uuid.uuid4().hex[:12]}")
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    voice_id = Column(String(36), ForeignKey("voices.id"), index=True, nullable=False)
    text_length = Column(Integer, default=0)
    audio_duration = Column(Float, default=0.0)
    watermark_id = Column(String(64), nullable=True)
    license_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<UsageLog {self.id} (user={self.user_id}, voice={self.voice_id})>"


class LicenseUsage(Base):
    """License-specific usage tracking model."""
    __tablename__ = "license_usage"

    id = Column(String(36), primary_key=True, default=lambda: f"lic_use_{uuid.uuid4().hex[:12]}")
    license_id = Column(String(36), ForeignKey("licenses.id"), index=True, nullable=False)
    token_id = Column(String(64), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    voice_id = Column(String(36), ForeignKey("voices.id"), index=True, nullable=False)
    text_length = Column(Integer, default=0)
    audio_duration = Column(Float, default=0.0)
    watermark_id = Column(String(64), nullable=True)
    used_at = Column(DateTime, default=datetime.utcnow)
    meta_json = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<LicenseUsage {self.id} (license={self.license_id})>"

