"""
Authentication endpoints for Whicoustic API v1.
Handles user registration, login, profile management, and API key generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from datetime import datetime, timedelta

from ...core.config import settings
from ...core.database import get_db
from ...core.security import (
    create_access_token, 
    verify_password, 
    get_password_hash,
    verify_token
)
from ...models.user import User
from ...schemas.auth import (
    UserCreate, 
    UserLogin, 
    UserResponse, 
    UserUpdate,
    Token,
    ApiKeyCreate,
    ApiKeyResponse
)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    token = credentials.credentials
    
    # MOCK AUTH KEY
    if settings.MOCK_AUTH_ENABLED and settings.ENVIRONMENT.lower() in {"development", "test"} and token == "mock-token-123":
        user = db.query(User).filter(User.email == "demo@whicoustic.com").first()
        if not user:
            # Auto-create mock user if missing
            password_hash = get_password_hash("demo123")
            user = User(
                username="demo_user",
                email="demo@whicoustic.com",
                hashed_password=password_hash,
                full_name="Demo User",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        dob=user_data.dob
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)

@router.post("/login", response_model=Token)
async def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    user = db.query(User).filter(
        (User.email == credentials.email)
    ).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile information."""
    return UserResponse.model_validate(current_user)

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile information."""
    
    update_data = profile_data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(current_user, key, value)
        
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)

@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new API key for the user."""
    # Implementation for API key generation
    # This would typically involve creating a secure random key
    # and storing it in the database with appropriate metadata
    
    api_key = f"whicoustic_{current_user.id}_{datetime.utcnow().timestamp()}"
    
    # In a real implementation, you'd save this to a separate APIKey model
    # For now, returning a placeholder response
    
    return ApiKeyResponse(
        key_id="key_123",
        key=api_key,
        name=key_data.name,
        key_prefix=api_key[:12] + "...",
        scopes=key_data.scopes,
        created_at=datetime.utcnow()
    )

@router.post("/verify-token")
async def verify_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify if the provided token is valid."""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return {"valid": True, "user_id": payload.get("sub")}  
security_optional = HTTPBearer(auto_error=False)  
  
async def get_optional_current_user(  
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),  
    db: Session = Depends(get_db)  
) -> Optional[User]:  
    if not credentials:  
        return None  
    try:  
        return await get_current_user(credentials, db)  
    except HTTPException:  
        return None 
