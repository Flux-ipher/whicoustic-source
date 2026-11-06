"""
Pydantic schemas for Whicoustic API request/response models.
"""

from .auth import *
from .voice import *
from .tts import *
from .license import *
from .watermark import *
from .escrow import *

__all__ = [
    # Auth schemas
    "UserCreate",
    "UserLogin", 
    "UserResponse",
    "Token",
    "ApiKeyCreate",
    "ApiKeyResponse",
    
    # Voice schemas
    "VoiceCreate",
    "VoiceResponse", 
    "VoiceUpdate",
    "VoiceUploadResponse",
    
    # TTS schemas
    "SynthesizeRequest",
    "SynthesizeResponse",
    "TTSJobResponse", 
    "VoiceParams",
    
    # License schemas
    "LicenseCreate",
    "LicenseResponse",
    "LicenseTokenRequest",
    "LicenseTokenResponse",
    "LicenseUsageResponse",
    
    # Watermark schemas
    "WatermarkVerificationResponse",
    "ForensicAnalysisResponse",

    # Escrow schemas
    "DisbursementItemResponse",
    "LicenseDisbursementsResponse",
    "DisbursementCreateRequest",
    "PlaybackRoyaltySplitRequest",
    "PlaybackRoyaltySplitResponse",
    "EscrowSummaryResponse"
]