from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserSyncIn(BaseModel):
    uid: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    photo_url: Optional[str] = None
    phone: Optional[str] = None
    provider_id: Optional[str] = None
    is_onboarded: Optional[bool] = None
    royalty_floor_pct: Optional[float] = None
    voice_category: Optional[str] = None
    vault_key: Optional[str] = None


class UserOut(BaseModel):
    id: str
    uid: Optional[str] = None
    email: Optional[str] = None  # Changed from Optional[EmailStr] to prevent serialization crash
    name: Optional[str] = None
    photo_url: Optional[str] = None
    phone: Optional[str] = None
    provider_id: Optional[str] = None
    is_onboarded: bool = False
    is_new_user: bool = False
    role: Optional[str] = None
    royalty_floor_pct: Optional[float] = None
    voice_category: Optional[str] = None
    vault_key: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @classmethod
    def from_model(
        cls,
        user: object,
        is_new_user: bool = False,
        provider_id: Optional[str] = None,
    ) -> "UserOut":
        is_onboarded = getattr(user, "is_onboarded", False)
        if is_onboarded is None:
            is_onboarded = False

        effective_is_new = getattr(user, "is_new_user", is_new_user)

        return cls.model_validate(
            {
                "id": str(getattr(user, "id", "")),
                "uid": getattr(user, "firebase_uid", None),
                "email": getattr(user, "email", None),
                "name": getattr(user, "full_name", None),
                "photo_url": getattr(user, "avatar", None),
                "phone": getattr(user, "phone", None),
                "provider_id": provider_id or getattr(user, "provider_id", None),
                "is_onboarded": bool(is_onboarded),
                "is_new_user": bool(effective_is_new),
                "role": getattr(user, "role", "user"),
                "royalty_floor_pct": getattr(user, "royalty_floor_pct", None),
                "voice_category": getattr(user, "voice_category", None),
                "vault_key": getattr(user, "vault_key", None),
            }
        )

