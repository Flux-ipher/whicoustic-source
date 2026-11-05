"""
Security utilities for Whicoustic platform.
Handles JWT tokens, password hashing, and authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt 
import secrets
import hashlib
import logging

logger = logging.getLogger(__name__)

import bcrypt
from .config import settings

# Default settings (should be overridden by config)
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def set_security_config(secret_key: str, algorithm: str = "HS256"):
    """Set global security configuration."""
    global SECRET_KEY, ALGORITHM
    SECRET_KEY = secret_key
    ALGORITHM = algorithm

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    try:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise

def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        logger.debug(f"Token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None

def create_api_key() -> str:
    """Generate a secure API key."""
    return f"whicoustic_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify API key against its hash."""
    try:
        return hash_api_key(api_key) == hashed_key
    except Exception as e:
        logger.error(f"API key verification error: {e}")
        return False

def generate_reset_token() -> str:
    """Generate password reset token."""
    return secrets.token_urlsafe(32)

def generate_verification_token() -> str:
    """Generate email verification token."""
    return secrets.token_urlsafe(32)

class SecurityUtils:
    """Security utilities class for dependency injection."""
    
    @staticmethod
    def create_token(data: Dict[str, Any], expires_minutes: int = 30) -> str:
        """Create JWT token with custom expiration."""
        expires_delta = timedelta(minutes=expires_minutes)
        return create_access_token(data, expires_delta)
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode JWT token."""
        return verify_token(token)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password."""
        return get_password_hash(password)
    
    @staticmethod
    def check_password(password: str, hashed: str) -> bool:
        """Check password against hash."""
        return verify_password(password, hashed)
    
    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """Generate API key and return both key and hash."""
        api_key = create_api_key()
        api_key_hash = hash_api_key(api_key)
        return api_key, api_key_hash

# Global security utils instance
security = SecurityUtils()