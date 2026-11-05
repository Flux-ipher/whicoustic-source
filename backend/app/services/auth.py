import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta
import json

from app.core.config import settings
from app.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class AuthService:
    """Firebase Authentication Service"""
    
    def __init__(self):
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        if not firebase_admin._apps:
            # Create Firebase credentials from environment variables
            firebase_config = {
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
                "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
                "client_email": settings.FIREBASE_CLIENT_EMAIL,
                "client_id": settings.FIREBASE_CLIENT_ID,
                "auth_uri": settings.FIREBASE_AUTH_URI,
                "token_uri": settings.FIREBASE_TOKEN_URI,
            }
            
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
    
    async def verify_firebase_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return decoded token"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Firebase token: {str(e)}"
            )
    
    async def get_or_create_user(self, db: AsyncSession, firebase_token: Dict[str, Any]) -> User:
        """Get existing user or create new user from Firebase token"""
        firebase_uid = firebase_token.get('uid')
        email = firebase_token.get('email')
        name = firebase_token.get('name', '')
        
        if not firebase_uid or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Firebase token missing required fields"
            )
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.firebase_uid == firebase_uid)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # Update last login
            existing_user.last_login = datetime.utcnow()
            await db.commit()
            return existing_user
        
        # Create new user
        # Generate username from email if not provided
        username = email.split('@')[0]
        counter = 1
        original_username = username
        
        # Ensure username is unique
        while True:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            if not result.scalar_one_or_none():
                break
            username = f"{original_username}{counter}"
            counter += 1
        
        new_user = User(
            email=email,
            firebase_uid=firebase_uid,
            username=username,
            display_name=name or username,
            is_verified=firebase_token.get('email_verified', False),
            last_login=datetime.utcnow(),
            email_verified_at=datetime.utcnow() if firebase_token.get('email_verified') else None
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return new_user
    
    def generate_jwt_token(self, user: User) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': str(user.id),
            'email': user.email,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    def generate_refresh_token(self, user: User) -> str:
        """Generate refresh token for user"""
        payload = {
            'user_id': str(user.id),
            'exp': datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            
            if payload.get('type') != 'access':
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def get_current_user(self, db: AsyncSession, token: str) -> User:
        """Get current user from JWT token"""
        payload = self.verify_jwt_token(token)
        user_id = payload.get('user_id')
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user information"
            )
        
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        return user


# Global auth service instance
auth_service = AuthService()
