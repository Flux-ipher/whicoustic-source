"""
Escrow and disbursement database models for Whicoustic platform.
Tracks licensing revenue, platform fee deductions (15%), creator net disbursements (85%),
and per-second playback royalty splits.
Compatible with SQLite (vcaas_dev2.db) and Supabase PostgreSQL.
"""

from datetime import datetime
import uuid
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base


class EscrowDisbursement(Base):
    """
    Escrow disbursement ledger entry.
    Tracks individual royalty streams, license payments, platform fee deductions (15%),
    and creator payouts across settled, pending, and disputed states.
    """
    __tablename__ = "escrow_disbursements"

    id = Column(String(36), primary_key=True, default=lambda: f"disb_{uuid.uuid4().hex[:12]}")
    license_id = Column(String(36), ForeignKey("licenses.id"), index=True, nullable=False)
    royalty_stream = Column(String(255), nullable=False)
    licensee = Column(String(255), nullable=False)
    gross_amount = Column(Float, nullable=False, default=0.0)
    platform_fee = Column(Float, nullable=False, default=0.0)
    net_amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(String(30), default="pending", nullable=False, index=True)  # 'settled', 'pending', 'disputed'
    playback_seconds = Column(Float, nullable=True, default=0.0)
    rate_per_second = Column(Float, nullable=True)
    tx_hash = Column(String(128), nullable=True)
    payment_method = Column(String(100), nullable=True)
    disbursed_at = Column(DateTime, nullable=True)
    dispute_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to License
    license = relationship("License", backref="disbursements")

    def __repr__(self) -> str:
        return f"<EscrowDisbursement {self.id} (license={self.license_id}, gross={self.gross_amount}, status={self.status})>"
