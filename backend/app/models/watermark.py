"""
Watermark verification model for Whicoustic platform.
"""

from datetime import datetime
import uuid
from sqlalchemy import Column, String, Boolean, Float, DateTime, JSON, ForeignKey
from ..core.database import Base


class WatermarkVerification(Base):
    """Watermark verification audit log model."""
    __tablename__ = "watermark_verifications"

    id = Column(String(36), primary_key=True, default=lambda: f"verify_{uuid.uuid4().hex[:12]}")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    original_filename = Column(String(255), nullable=True)
    detection_method = Column(String(50), default="unknown")
    watermark_found = Column(Boolean, default=False)
    watermark_id = Column(String(64), nullable=True)
    license_id = Column(String(64), nullable=True)
    confidence_score = Column(Float, default=0.0)
    detection_metadata = Column(JSON, nullable=True)
    verified_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<WatermarkVerification {self.id} found={self.watermark_found}>"

