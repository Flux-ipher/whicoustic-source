"""
Voice and Voice Sample models and enums for Whicoustic platform.
"""

from datetime import datetime
from enum import Enum
import uuid
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, ForeignKey
from ..core.database import Base


class VoiceStatus(str, Enum):
    """Voice processing and training status."""
    PENDING = "pending"
    PROCESSING = "processing"
    TRAINING = "training"
    TRAINED = "trained"
    READY = "ready"
    FAILED = "failed"


class VoiceQuality(str, Enum):
    """Voice quality classification."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class Voice(Base):
    """Voice profile model."""
    __tablename__ = "voices"

    id = Column(String(36), primary_key=True, default=lambda: f"voice_{uuid.uuid4().hex[:12]}")
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    original_filename = Column(String(255), nullable=True)
    file_path = Column(String(512), nullable=True)
    speaker_embedding = Column(JSON, nullable=True)
    duration = Column(Float, default=0.0)
    sample_rate = Column(Integer, default=22050)
    file_size = Column(Integer, nullable=True)
    status = Column(String(50), default="pending")
    quality_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Voice {self.name} ({self.id})>"


class VoiceSample(Base):
    """Voice sample model for training and processing pipelines."""
    __tablename__ = "voice_samples"

    id = Column(String(36), primary_key=True, default=lambda: f"sample_{uuid.uuid4().hex[:12]}")
    voice_id = Column(String(36), ForeignKey("voices.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    file_path = Column(String(512), nullable=True)
    model_path = Column(String(512), nullable=True)
    duration = Column(Float, default=0.0)
    sample_rate = Column(Integer, default=22050)
    channels = Column(Integer, default=1)
    status = Column(String(50), default=VoiceStatus.PENDING)
    quality_score = Column(Float, nullable=True)
    quality_level = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<VoiceSample {self.id} (Status: {self.status})>"

