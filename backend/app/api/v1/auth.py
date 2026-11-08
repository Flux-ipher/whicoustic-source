"""
Authentication endpoints for Whicoustic API v1.
Handles user registration, login, profile management, and API key generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
import uuid

from datetime import datetime, timedelta

from ...core.config import settings
from ...core.database import get_db
from ...core.security import (
    create_access_token, 
    verify_password, 
    get_password_hash,
    verify_token
)
from ...core.firebase_auth import verify_firebase_token
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
security = HTTPBearer(auto_error=False)


def _ensure_unique_username(db: Session, base_name: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in (base_name or "user")).strip("_-") or "user"
    candidate = cleaned[:50]
    suffix = 1
    while db.query(User).filter(User.username == candidate).first():
        suffix_text = f"_{suffix}"
        max_len = max(1, 50 - len(suffix_text))
        candidate = f"{cleaned[:max_len]}{suffix_text}"
        suffix += 1
    return candidate


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Unified authentication dependency supporting Firebase ID tokens, local JWTs, and dev mock."""
    if credentials is None or not credentials.scheme or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()

    # 1. Dev Mock Bypass
    if settings.MOCK_AUTH_ENABLED and settings.ENVIRONMENT.lower() in {"development", "test"} and token == "mock-token-123":
        user = db.query(User).filter(User.email == "demo@whicoustic.com").first()
        if not user:
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

    # 2. Dual Verification: Try Firebase ID token, then fallback to local HS256 JWT
    claims = None
    is_firebase = False

    try:
        claims = verify_firebase_token(token)
        is_firebase = True
    except HTTPException:
        claims = None
    except Exception:
        claims = None

    if claims is None:
        payload = verify_token(token)
        if payload:
            claims = payload
            is_firebase = False

    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. User Resolution & Auto-Provisioning
    user = None
    if not is_firebase:
        user_id = claims.get("sub")
        if user_id:
            user = db.query(User).filter(User.id == str(user_id)).first()
    else:
        uid = (claims.get("uid") or claims.get("user_id") or claims.get("sub") or "").strip()
        email = (claims.get("email") or "").strip()

        if uid:
            user = db.query(User).filter(User.firebase_uid == uid).first()
        if not user and email:
            user = db.query(User).filter(User.email.ilike(email)).first()
            if user and user.firebase_uid and uid and user.firebase_uid != uid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account with this email is already linked to another identity",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            if user and uid and not user.firebase_uid:
                user.firebase_uid = uid
                try:
                    db.commit()
                    db.refresh(user)
                except Exception:
                    db.rollback()

        # Auto-provision user if verified via Firebase but not yet present in DB
        if not user:
            name = claims.get("name") or (email.split("@")[0] if email else "user")
            username = _ensure_unique_username(db, name)
            safe_email = email or f"{uid}@auth.whicoustic.xyz"
            user = User(
                username=username,
                email=safe_email,
                firebase_uid=uid or None,
                full_name=claims.get("name"),
                avatar=claims.get("picture"),
                is_active=True,
                is_onboarded=False,
            )
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
            except IntegrityError:
                db.rollback()
                user = db.query(User).filter(User.firebase_uid == uid).first() if uid else None
                if not user and email:
                    user = db.query(User).filter(User.email.ilike(email)).first()
                    if user and user.firebase_uid and uid and user.firebase_uid != uid:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Account with this email is already linked to another identity",
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                # If still not found, collision was on username -> retry with randomized suffix
                if not user:
                    cleaned_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in (name or "user")).strip("_-") or "user"
                    for _ in range(5):
                        suffix = f"_{uuid.uuid4().hex[:6]}"
                        retry_username = f"{cleaned_name[:50 - len(suffix)]}{suffix}"
                        user = User(
                            username=retry_username,
                            email=safe_email,
                            firebase_uid=uid or None,
                            full_name=claims.get("name"),
                            avatar=claims.get("picture"),
                            is_active=True,
                            is_onboarded=False,
                        )
                        db.add(user)
                        try:
                            db.commit()
                            db.refresh(user)
                            break
                        except IntegrityError:
                            db.rollback()
                            user = db.query(User).filter(User.firebase_uid == uid).first() if uid else None
                            if not user and email:
                                user = db.query(User).filter(User.email.ilike(email)).first()
                                if user and user.firebase_uid and uid and user.firebase_uid != uid:
                                    raise HTTPException(
                                        status_code=status.HTTP_401_UNAUTHORIZED,
                                        detail="Account with this email is already linked to another identity",
                                        headers={"WWW-Authenticate": "Bearer"},
                                    )
                            if user:
                                break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account could not be resolved or provisioned",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Verify if the provided token is valid."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
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
