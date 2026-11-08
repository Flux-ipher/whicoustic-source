from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.firebase_auth import get_current_user
from app.models.user import User
from app.schemas.user import UserOut, UserSyncIn

router = APIRouter()


def _ensure_unique_username(db: Session, base_username: str) -> str:
    username = base_username[:50]
    candidate = username
    suffix = 1
    while db.query(User).filter(User.username == candidate).first():
        suffix_text = f"_{suffix}"
        max_length = max(1, 50 - len(suffix_text))
        candidate = f"{username[:max_length]}{suffix_text}"
        suffix += 1
    return candidate


@router.post('/users/sync', response_model=UserOut)
@router.post('/users/sync/', response_model=UserOut)
def sync_user(
    payload: UserSyncIn,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user),
):
    # 1. Canonical UID derivation and token ownership validation (BOLA / IDOR Defense)
    token_uid = (claims.get('uid') or claims.get('user_id') or claims.get('sub') or '').strip() or None
    payload_uid = (payload.uid or '').strip() or None

    if payload_uid and token_uid and payload_uid != token_uid:
        raise HTTPException(
            status_code=403,
            detail="Payload UID does not match authenticated token",
        )

    uid = token_uid or payload_uid

    # 2. Canonical Email derivation and token ownership validation
    token_email = (claims.get('email') or '').strip() or None
    payload_email = (payload.email or '').strip() or None

    if payload_email and token_email and payload_email.lower() != token_email.lower():
        raise HTTPException(
            status_code=403,
            detail="Payload email does not match authenticated token email",
        )

    email = token_email or payload_email
    name = payload.name or claims.get('name') or claims.get('full_name')
    photo_url = payload.photo_url or claims.get('picture')
    phone = payload.phone or claims.get('phone_number') or claims.get('phone')
    provider_id = payload.provider_id or (
        claims.get('firebase', {}).get('sign_in_provider')
        if isinstance(claims.get('firebase'), dict)
        else None
    )

    if not uid and not email:
        raise HTTPException(status_code=400, detail='uid or email required')

    # 3. User lookup with account takeover guard
    user = None
    if uid:
        user = db.query(User).filter(User.firebase_uid == uid).first()
    if not user and email:
        user = db.query(User).filter(User.email.ilike(email)).first()
        # Account Takeover Prevention: If found by email, ensure it's not already linked to another Firebase UID
        if user and user.firebase_uid and uid and user.firebase_uid != uid:
            raise HTTPException(
                status_code=409,
                detail="Account with this email is already linked to another Firebase identity",
            )

    is_new_user = (user is None)

    if user:
        if uid and not user.firebase_uid:
            user.firebase_uid = uid
        if email and user.email.lower() != email.lower():
            # Prevent unhandled IntegrityError on duplicate email collision
            conflict_user = db.query(User).filter(
                User.email.ilike(email),
                User.id != user.id,
            ).first()
            if conflict_user:
                raise HTTPException(
                    status_code=409,
                    detail="Email is already associated with another account",
                )
            user.email = email
        if name:
            user.full_name = name
        if photo_url:
            user.avatar = photo_url
        if phone:
            user.phone = phone

        # Monotonic onboarding preservation: never demote True to False
        if payload.is_onboarded is True:
            if not user.is_onboarded:
                user.is_onboarded = True
                user.onboarded_at = datetime.utcnow()
            elif not user.onboarded_at:
                user.onboarded_at = datetime.utcnow()

        if payload.royalty_floor_pct is not None:
            user.royalty_floor_pct = payload.royalty_floor_pct
        if payload.voice_category is not None:
            user.voice_category = payload.voice_category
        if payload.vault_key is not None:
            user.vault_key = payload.vault_key
    else:
        # 4. RFC-compliant synthetic email generation
        if email:
            safe_email = email
        elif uid:
            clean_uid = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in uid).strip("-_.") or "user"
            safe_email = f"{clean_uid}@auth.whicoustic.xyz"
        else:
            safe_email = f"user_{uuid.uuid4().hex[:8]}@auth.whicoustic.xyz"

        # 5. Strictly sanitize username conforming to ^[a-zA-Z0-9_-]+$
        base_name = (name or (email.split('@', 1)[0] if email else 'user')).strip()
        base_username = ''.join(ch if ch.isalnum() or ch in {'_', '-'} else '_' for ch in (base_name or 'user')).strip('_')
        safe_uid = ''.join(ch for ch in (uid or '') if ch.isalnum() or ch in {'_', '-'})
        if not base_username:
            base_username = f"user_{safe_uid[:12]}" if safe_uid else 'user'
        if len(base_username) < 3:
            base_username = f"{base_username}_{safe_uid[:6] if safe_uid else 'user'}"

        username = _ensure_unique_username(db, base_username)
        new_is_onboarded = bool(payload.is_onboarded) if payload.is_onboarded is not None else False
        new_onboarded_at = datetime.utcnow() if new_is_onboarded else None
        new_royalty_floor_pct = payload.royalty_floor_pct if payload.royalty_floor_pct is not None else 18.5

        user = User(
            username=username,
            email=safe_email,
            firebase_uid=uid,
            full_name=name,
            avatar=photo_url,
            phone=phone,
            is_active=True,
            is_onboarded=new_is_onboarded,
            onboarded_at=new_onboarded_at,
            royalty_floor_pct=new_royalty_floor_pct,
            voice_category=payload.voice_category,
            vault_key=payload.vault_key,
        )
        db.add(user)

    # 6. Atomic commit and concurrency recovery
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        if is_new_user:
            # Race condition: another thread created this user concurrently
            existing_user = None
            if uid:
                existing_user = db.query(User).filter(User.firebase_uid == uid).first()
            if not existing_user and email:
                existing_user = db.query(User).filter(User.email.ilike(email)).first()

            if existing_user:
                user = existing_user
                is_new_user = False
                # Merge onboarding if requested and not yet set
                if payload.is_onboarded is True:
                    if not user.is_onboarded:
                        user.is_onboarded = True
                        user.onboarded_at = datetime.utcnow()
                    elif not user.onboarded_at:
                        user.onboarded_at = datetime.utcnow()
                    try:
                        db.commit()
                        db.refresh(user)
                    except Exception:
                        db.rollback()
            else:
                # Concurrent username collision: retry with unique suffix
                created = False
                for _ in range(5):
                    suffix = f"_{uuid.uuid4().hex[:6]}"
                    retry_username = f"{base_username[:50 - len(suffix)]}{suffix}"
                    user = User(
                        username=retry_username,
                        email=safe_email,
                        firebase_uid=uid,
                        full_name=name,
                        avatar=photo_url,
                        phone=phone,
                        is_active=True,
                        is_onboarded=new_is_onboarded,
                        onboarded_at=new_onboarded_at,
                        royalty_floor_pct=new_royalty_floor_pct,
                        voice_category=payload.voice_category,
                        vault_key=payload.vault_key,
                    )
                    db.add(user)
                    try:
                        db.commit()
                        db.refresh(user)
                        created = True
                        break
                    except IntegrityError:
                        db.rollback()
                        user = db.query(User).filter(User.firebase_uid == uid).first() if uid else None
                        if not user and email:
                            user = db.query(User).filter(User.email.ilike(email)).first()
                        if user:
                            is_new_user = False
                            created = True
                            break

                if not created:
                    raise HTTPException(
                        status_code=409,
                        detail="Conflict persisting user record due to concurrent database activity",
                    )
        else:
            raise HTTPException(
                status_code=409,
                detail="Unique constraint violation during user update",
            )

    return UserOut.from_model(user, is_new_user=is_new_user, provider_id=provider_id)
