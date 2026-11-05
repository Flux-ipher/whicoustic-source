from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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
def sync_user(
    payload: UserSyncIn,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user),
):
    uid = payload.uid or claims.get('uid') or claims.get('user_id')
    email = (payload.email or claims.get('email') or '').strip() or None
    name = payload.name or claims.get('name') or claims.get('full_name')
    photo_url = payload.photo_url or claims.get('picture')
    phone = payload.phone or claims.get('phone_number') or claims.get('phone')

    if not uid and not email:
        raise HTTPException(status_code=400, detail='uid or email required')

    user = None
    if uid:
        user = db.query(User).filter(User.firebase_uid == uid).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    if user:
        if uid:
            user.firebase_uid = uid
        if email:
            user.email = email
        if name:
            user.full_name = name
        if photo_url:
            user.avatar = photo_url
        if phone:
            user.phone = phone
    else:
        if email:
            safe_email = email
        elif uid:
            safe_email = f"{uid}@firebase.local"
        else:
            safe_email = "user@firebase.local"

        base_name = (name or (email.split('@', 1)[0] if email else 'user')).strip()
        base_username = ''.join(ch if ch.isalnum() or ch in {'_', '-'} else '_' for ch in (base_name or 'user')).strip('_')
        if not base_username:
            base_username = 'user'
        if email:
            base_username = email.split('@', 1)[0]
        if uid and not base_username:
            base_username = f"user_{uid[:12]}"
        if len(base_username) < 3:
            base_username = f"{base_username}_{uid[:6] if uid else 'user'}"

        username = _ensure_unique_username(db, base_username)
        user = User(
            username=username,
            email=safe_email,
            firebase_uid=uid,
            full_name=name,
            avatar=photo_url,
            phone=phone,
            is_active=True,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return UserOut.from_model(user)
