"""
Watermark verification-related Pydantic schemas for Whicoustic API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class WatermarkVerificationResponse(BaseModel):
    """Schema for watermark verification response."""
    verification_id: str
    watermark_found: bool
    watermark_id: Optional[str] = None
    license_id: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    detection_method: str
    timestamp: Optional[str] = None
    signature_valid: bool = False
    verification_time: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "verification_id": "verify_abc123def456",
                "watermark_found": True,
                "watermark_id": "wm_xyz789abc123",
                "license_id": "lic_commercial_001",
                "confidence_score": 0.95,
                "detection_method": "mvp_sine",
                "signature_valid": True,
                "verification_time": "2023-12-01T12:00:00Z"
            }
        }

class ForensicAnalysisResponse(BaseModel):
    """Schema for comprehensive forensic analysis response."""
    analysis_id: str
    watermark_found: bool
    watermark_details: Optional[Dict[str, Any]] = None
    audio_integrity: Dict[str, Any]
    manipulation_detected: bool
    manipulation_details: List[str] = []
    metadata_analysis: Dict[str, Any]
    spectral_analysis: Dict[str, Any]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    analysis_depth: str
    analyzed_at: datetime
    recommendations: List[str] = []
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "analysis_id": "forensic_abc123def456",
                "watermark_found": True,
                "watermark_details": {
                    "watermark_id": "wm_xyz789abc123",
                    "detection_method": "robust_spread_spectrum"
                },
                "audio_integrity": {
                    "tampering_detected": False,
                    "quality_score": 0.89
                },
                "manipulation_detected": False,
                "confidence_score": 0.92,
                "analysis_depth": "standard",
                "analyzed_at": "2023-12-01T12:00:00Z"
            }
        }
