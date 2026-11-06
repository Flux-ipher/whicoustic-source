"""
Pydantic schemas for Escrow and Royalty Disbursements in Whicoustic API.
Standardizes gross escrow, 15% platform fee, 85% net creator disbursement,
and per-second playback splits according to PROJECT.md § Backend Escrow Disbursement Contract.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DisbursementItemResponse(BaseModel):
    """Schema for individual disbursement record matching PROJECT.md contract."""
    id: str
    royalty_stream: str
    licensee: str
    gross_amount: float
    platform_fee: float
    net_amount: float
    status: str  # 'settled', 'pending', 'disputed'
    disbursed_at: Optional[str] = None

    class Config:
        from_attributes = True


class LicenseDisbursementsResponse(BaseModel):
    """Schema for license escrow disbursement response matching PROJECT.md contract."""
    license_id: str
    gross_escrow: float
    platform_fee: float
    net_disbursement: float
    currency: str = "USD"
    disbursements: List[DisbursementItemResponse]

    class Config:
        from_attributes = True


class DisbursementCreateRequest(BaseModel):
    """Schema for creating a new escrow disbursement entry."""
    royalty_stream: str = Field(..., min_length=1, max_length=255)
    licensee: str = Field(..., min_length=1, max_length=255)
    gross_amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    status: str = Field(default="pending", pattern=r"^(settled|pending|disputed)$")
    playback_seconds: Optional[float] = Field(None, ge=0)
    rate_per_second: Optional[float] = Field(None, ge=0)
    tx_hash: Optional[str] = None
    payment_method: Optional[str] = None


class PlaybackRoyaltySplitRequest(BaseModel):
    """Schema for calculating per-second playback royalty splits."""
    duration_seconds: float = Field(..., gt=0)
    rate_per_second: float = Field(default=0.05, gt=0)
    platform_fee_percent: float = Field(default=15.0, ge=0, le=100)


class PlaybackRoyaltySplitResponse(BaseModel):
    """Schema for per-second playback royalty split calculation result."""
    duration_seconds: float
    rate_per_second: float
    gross_amount: float
    platform_fee: float
    net_creator_amount: float
    platform_fee_percent: float = 15.0
    creator_percent: float = 85.0


class EscrowSummaryResponse(BaseModel):
    """Schema for aggregated escrow balances by status."""
    license_id: str
    currency: str = "USD"
    total_gross: float
    total_platform_fee: float
    total_net: float
    settled: Dict[str, Any]
    pending: Dict[str, Any]
    disputed: Dict[str, Any]
