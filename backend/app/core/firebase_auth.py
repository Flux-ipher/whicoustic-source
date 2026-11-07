"""
Firebase ID token verification utilities.

This module verifies Firebase ID tokens and exposes a FastAPI dependency
that returns the authenticated user's claims. It supports mock dev fallback (mock-token-123)
when in development or test environments.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

try:
    import firebase_admin
    from firebase_admin import auth as fb_auth
    from firebase_admin import credentials
except Exception:  # pragma: no cover - module import guard for environments without firebase_admin
    firebase_admin = None  # type: ignore
    fb_auth = None  # type: ignore
    credentials = None  # type: ignore

try:
    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_requests
except Exception:  # pragma: no cover
    google_id_token = None  # type: ignore
    google_requests = None  # type: ignore


security = HTTPBearer(auto_error=False)


class FirebaseNotConfigured(Exception):
    pass


@lru_cache(maxsize=1)
def _ensure_firebase_app():
    """Initialize Firebase Admin app once using service account from env.

    Expects FIREBASE_* variables to be present (see backend/.env.example).
    """
    if firebase_admin is None:
        raise FirebaseNotConfigured("firebase_admin is not installed")

    if firebase_admin._apps:  # already initialized
        return firebase_admin.get_app()

    # Build service account dictionary from env (escaped newlines handled)
    private_key = settings.FIREBASE_PRIVATE_KEY
    if not private_key or private_key == "dummy":
        raise FirebaseNotConfigured("FIREBASE_PRIVATE_KEY is not configured or dummy")

    private_key = private_key.replace("\\n", "\n")

    cred_info = {
        "type": "service_account",
        "project_id": settings.FIREBASE_PROJECT_ID,
        "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
        "private_key": private_key,
        "client_email": settings.FIREBASE_CLIENT_EMAIL,
        "client_id": settings.FIREBASE_CLIENT_ID,
        "auth_uri": settings.FIREBASE_AUTH_URI,
        "token_uri": settings.FIREBASE_TOKEN_URI,
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{settings.FIREBASE_CLIENT_EMAIL}",
    }

    try:
        cred = credentials.Certificate(cred_info)
        return firebase_admin.initialize_app(cred)
    except Exception as exc:
        raise FirebaseNotConfigured(f"Failed to initialize Firebase credentials: {exc}")


def _is_admin_claims(claims: Dict) -> bool:
    """Check if claims or allowlists mark user as admin."""
    admin_emails = [e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()]
    admin_uids = [u.strip() for u in os.getenv("ADMIN_UIDS", "").split(",") if u.strip()]

    email = (claims.get("email") or "").lower()
    uid = claims.get("uid") or claims.get("user_id")

    return (email and email in admin_emails) or (uid and uid in admin_uids) or bool(claims.get("admin") or claims.get("is_admin"))


def verify_firebase_token(token: str) -> Dict:
    """Verify a Firebase ID token or return mock user dict if in dev/test with mock-token-123."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    # Support mock auth when enabled (support mock-token-123)
    if settings.MOCK_AUTH_ENABLED and token == "mock-token-123":
        return {
            "uid": "demo-user-123",
            "email": "demo@whicoustic.com",
            "name": "Demo User",
            "picture": None,
            "is_admin": True,
        }

    decoded = None

    # First attempt verification via firebase_admin if installed and configured
    if firebase_admin is not None:
        try:
            _ensure_firebase_app()
            decoded = fb_auth.verify_id_token(token, check_revoked=False)
        except FirebaseNotConfigured:
            decoded = None
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    # Fallback to google.oauth2.id_token when firebase_admin is None or unconfigured
    if decoded is None:
        if google_id_token is not None and google_requests is not None:
            try:
                req = google_requests.Request()
                audience = settings.FIREBASE_PROJECT_ID if (settings.FIREBASE_PROJECT_ID and settings.FIREBASE_PROJECT_ID != "dummy") else None
                try:
                    decoded = google_id_token.verify_firebase_token(token, req, audience=audience)
                except Exception:
                    if audience:
                        decoded = google_id_token.verify_firebase_token(token, req, audience=None)
                    else:
                        raise
            except Exception:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Firebase authentication is not configured and fallback verifier is unavailable",
            )

    # Normalize and augment
    uid = decoded.get("uid") or decoded.get("user_id") or decoded.get("sub")
    claims = {
        "uid": uid,
        "email": decoded.get("email"),
        "name": decoded.get("name"),
        "picture": decoded.get("picture"),
        **decoded,
    }
    if "uid" not in claims or not claims["uid"]:
        claims["uid"] = uid
    claims["is_admin"] = _is_admin_claims(claims)
    return claims


async def get_current_user(credentials_hdr: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict:
    """Validate Authorization: Bearer <Firebase ID token> and return claims.

    Raises 401 if missing/invalid. Adds `is_admin` to claims if allowlisted.
    """
    if credentials_hdr is None or not credentials_hdr.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    return verify_firebase_token(credentials_hdr.credentials)