"""
License model for Whicoustic platform.
"""

from datetime import datetime
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, Text, JSON, ForeignKey
from ..core.database import Base


class License(Base):
    """Voice license model."""
    __tablename__ = "licenses"

    id = Column(String(36), primary_key=True, default=lambda: f"lic_{uuid.uuid4().hex[:16]}")
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    voice_id = Column(String(36), ForeignKey("voices.id"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    license_type = Column(String(50), nullable=False)
    price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="USD")
    duration_days = Column(Integer, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    territory = Column(JSON, nullable=True)
    allowed_use_cases = Column(JSON, nullable=True)
    restrictions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<License {self.name} ({self.id})>"

