"""
License service for Whicoustic platform.
Handles license token generation, validation, and usage tracking.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class LicenseService:
    """Service for handling license operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.secret_key = "whicoustic_license_secret"  # Should come from config
        
    async def generate_license_token(
        self,
        license_id: str,
        purchaser_email: str,
        purchaser_name: Optional[str] = None,
        purchase_amount: Optional[float] = None,
        custom_terms: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a license token for a purchaser."""
        
        # Create token payload
        payload = {
            "license_id": license_id,
            "purchaser_email": purchaser_email,
            "purchaser_name": purchaser_name,
            "purchase_amount": float(purchase_amount) if isinstance(purchase_amount, Decimal) else purchase_amount,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
        }
        
        # Add custom terms if provided
        if custom_terms:
            payload["custom_terms"] = custom_terms
        
        # Generate JWT token
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        return {
            "token": token,
            "token_id": f"token_{license_id}_{hash(purchaser_email) % 10000}",
            "expires_at": payload["expires_at"]
        }
    
    async def validate_license_token(
        self, 
        token: str, 
        voice_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Validate a license token."""
        
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Check if token is expired
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.utcnow() > expires_at:
                return None
            
            # Return validation result
            return {
                "license_id": payload["license_id"],
                "voice_id": voice_id,
                "purchaser_email": payload["purchaser_email"],
                "expires_at": payload["expires_at"],
                "usage_remaining": -1,  # Unlimited for now
                "allowed_use_cases": ["commercial", "personal"],
                "territory": ["worldwide"]
            }
            
        except jwt.ExpiredSignatureError:
            logger.debug("License token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid license token: {e}")
            return None
        except Exception as e:
            logger.error(f"License token validation error: {e}")
            return None