from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserSyncIn(BaseModel):
    uid: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    photo_url: Optional[str] = None
    phone: Optional[str] = None
    provider_id: Optional[str] = None


class UserOut(BaseModel):
    id: str
    uid: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    photo_url: Optional[str] = None
    phone: Optional[str] = None
    provider_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @classmethod
    def from_model(cls, user: object) -> "UserOut":
        return cls.model_validate(
            {
                "id": getattr(user, "id", None),
                "uid": getattr(user, "firebase_uid", None),
                "email": getattr(user, "email", None),
                "name": getattr(user, "full_name", None),
                "photo_url": getattr(user, "avatar", None),
                "phone": getattr(user, "phone", None),
                "provider_id": None,
            }
        )
