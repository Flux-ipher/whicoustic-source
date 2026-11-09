"""
Milestone 7 Automated Unit & Integration Tests: Production 401 Auth Chain Alignment & Fix.
========================================================================================

Verifies:
1. Trailing slash invariance:
   - GET /api/v1/voices and GET /api/v1/voices/ both return 200 (no 307 redirect).
   - GET /api/v1/licenses and GET /api/v1/licenses/ both return 200 (no 307 redirect).
2. CORS preflight OPTIONS requests:
   - Returns 200 with Access-Control-Allow-Origin, Allow-Credentials, and reflects Authorization header.
   - Verified for origins https://whicoustic.ai, https://app.whicoustic.ai, https://api.whicoustic.xyz, and https://whicoustic.onrender.com.
3. Multi-provider authentication verification:
   - Valid Firebase ID token accepted on /api/v1/voices, /api/v1/licenses, and /api/v1/voices/upload.
   - Auto-provisioning of new Firebase user record into database.
   - Linking of existing user by email when matching Firebase token arrives.
   - Local HS256 JWT access token verification.
   - Development mock token 'mock-token-123' bypass.
4. Authentication failure modes:
   - Missing Authorization header -> 401 with WWW-Authenticate: Bearer.
   - Non-bearer scheme (e.g. Basic) -> 401 with WWW-Authenticate: Bearer.
   - Malformed or invalid JWT token -> 401 with WWW-Authenticate: Bearer.
   - Expired JWT token -> 401 with WWW-Authenticate: Bearer.
   - Disabled user account -> 403 Forbidden.
5. Milestone 7 Remediation (Iteration 2):
   - Account takeover prevention: Mismatched UID on existing email rejected with HTTP 401.
   - Auto-provisioning collision recovery: Concurrency race on username retries with unique randomized suffix.
   - Defense-in-depth mock token rejection: Production mode strictly rejects mock-token-123 even if MOCK_AUTH_ENABLED is True.
"""

import io
import os
import sys
import uuid
import wave
import struct
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

# Ensure environment is configured for test mode with mock auth capability
os.environ["ENVIRONMENT"] = "development"
os.environ["MOCK_AUTH_ENABLED"] = "true"
os.environ["SECRET_KEY"] = "milestone7_auth_chain_test_secret_key_32chars!"

# Ensure D:\.pip-packages is in sys.path so pytest and its dependencies are loaded
if "D:\\.pip-packages" not in sys.path:
    sys.path.insert(0, "D:\\.pip-packages")

# Ensure backend root is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash, set_security_config
from app.models.user import User
from app.models.voice import Voice
from app.models.license import License
from app.main import app

settings.ENVIRONMENT = "development"
settings.MOCK_AUTH_ENABLED = True

# Ensure security config is initialized with valid HMAC key for JWT operations
set_security_config(
    settings.SECRET_KEY or "milestone7_auth_chain_test_secret_key_32chars!",
    getattr(settings, "JWT_ALGORITHM", "HS256") or "HS256"
)


# ---------------------------------------------------------------------------
# Test Fixtures & In-Memory SQLite Setup
# ---------------------------------------------------------------------------
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, follow_redirects=False)


def _generate_wav_bytes(duration_sec: float = 6.0, sample_rate: int = 16000) -> bytes:
    """Generate a clean in-memory PCM 16-bit mono WAV file."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        total_samples = int(duration_sec * sample_rate)
        samples = [int(1000 * (i % 16)) for i in range(total_samples)]
        raw_data = struct.pack(f"<{len(samples)}h", *samples)
        wf.writeframes(raw_data)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tests: Missing & Malformed Bearer Token
# ---------------------------------------------------------------------------
def test_missing_bearer_token_returns_401_with_www_authenticate():
    """Verify missing Authorization header triggers 401 with standard WWW-Authenticate header."""
    response = client.get("/api/v1/voices")
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert "Bearer" in response.headers["WWW-Authenticate"]
    assert "Missing or malformed bearer token" in response.json()["detail"]


def test_non_bearer_scheme_returns_401():
    """Verify non-bearer authorization scheme is rejected with 401."""
    response = client.get("/api/v1/voices", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.json()["detail"] == "Missing or malformed bearer token"


def test_malformed_token_returns_401():
    """Verify arbitrary malformed token string returns 401."""
    response = client.get("/api/v1/voices", headers={"Authorization": "Bearer not-a-valid-token-at-all"})
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert "Invalid or expired authentication credentials" in response.json()["detail"]


def test_expired_local_jwt_returns_401():
    """Verify expired local JWT is rejected with 401."""
    expired_token = create_access_token(
        data={"sub": "user_expired_123"},
        expires_delta=timedelta(seconds=-3600),
    )
    response = client.get("/api/v1/voices", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    assert "Invalid or expired authentication credentials" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Tests: Development Mock Token
# ---------------------------------------------------------------------------
def test_dev_mock_token_success():
    """Verify 'mock-token-123' bypass functions in dev/test environment."""
    response = client.get("/api/v1/voices", headers={"Authorization": "Bearer mock-token-123"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# Tests: Local HS256 JWT Verification
# ---------------------------------------------------------------------------
def test_local_hs256_jwt_verification():
    """Verify valid local HS256 JWT authenticates successfully and loads user."""
    db = TestingSessionLocal()
    user = User(
        id=str(uuid.uuid4()),
        username="local_jwt_user",
        email="local_jwt@whicoustic.xyz",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    response = client.get("/api/v1/voices", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    db.close()


def test_disabled_user_account_returns_403_forbidden():
    """Verify deactivated user account returns HTTP 403 Forbidden."""
    db = TestingSessionLocal()
    disabled_user = User(
        id=str(uuid.uuid4()),
        username="disabled_user",
        email="disabled@whicoustic.xyz",
        hashed_password=get_password_hash("password123"),
        is_active=False,
    )
    db.add(disabled_user)
    db.commit()
    db.refresh(disabled_user)

    token = create_access_token(data={"sub": str(disabled_user.id)})
    response = client.get("/api/v1/voices", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert "Account is disabled" in response.json()["detail"]
    db.close()


# ---------------------------------------------------------------------------
# Tests: Firebase ID Token & Auto-Provisioning
# ---------------------------------------------------------------------------
def test_firebase_token_auto_provisions_new_user():
    """Verify valid Firebase ID token auto-provisions user record if not in DB."""
    uid = f"fb_new_{uuid.uuid4().hex[:8]}"
    email = f"auto_provisioned_{uuid.uuid4().hex[:6]}@whicoustic.xyz"
    mock_claims = {
        "uid": uid,
        "email": email,
        "name": "Auto Provisioned User",
        "picture": "https://whicoustic.xyz/avatar.png",
    }

    with patch("app.api.v1.auth.verify_firebase_token", return_value=mock_claims):
        response = client.get("/api/v1/voices", headers={"Authorization": "Bearer mocked-firebase-id-token"})
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    # Verify user record was persisted in database with correct attributes
    db = TestingSessionLocal()
    user_in_db = db.query(User).filter(User.firebase_uid == uid).first()
    assert user_in_db is not None
    assert user_in_db.email == email
    assert user_in_db.full_name == "Auto Provisioned User"
    assert user_in_db.is_active is True
    assert user_in_db.is_onboarded is False
    db.close()


def test_firebase_token_links_existing_user_by_email():
    """Verify Firebase token links firebase_uid if user exists with matching email."""
    db = TestingSessionLocal()
    existing_user = User(
        id=str(uuid.uuid4()),
        username="legacy_email_user",
        email="link_me@whicoustic.xyz",
        firebase_uid=None,
        is_active=True,
    )
    db.add(existing_user)
    db.commit()
    db.refresh(existing_user)

    uid = f"fb_link_{uuid.uuid4().hex[:8]}"
    mock_claims = {
        "uid": uid,
        "email": "link_me@whicoustic.xyz",
        "name": "Linked Email User",
    }

    with patch("app.api.v1.auth.verify_firebase_token", return_value=mock_claims):
        response = client.get("/api/v1/voices", headers={"Authorization": "Bearer mock-fb-token-linking"})
        assert response.status_code == 200

    db.refresh(existing_user)
    assert existing_user.firebase_uid == uid
    db.close()


# ---------------------------------------------------------------------------
# Tests: Trailing Slash Invariance (No 307 Redirects)
# ---------------------------------------------------------------------------
def test_trailing_slash_invariance_voices():
    """Verify /api/v1/voices and /api/v1/voices/ both return HTTP 200 without 307 redirects."""
    mock_claims = {
        "uid": "fb_slash_tester",
        "email": "slash_tester@whicoustic.xyz",
        "name": "Slash Tester",
    }

    with patch("app.api.v1.auth.verify_firebase_token", return_value=mock_claims):
        # Without trailing slash
        resp1 = client.get("/api/v1/voices", headers={"Authorization": "Bearer mock-fb-token"})
        assert resp1.status_code == 200, f"Expected 200 without slash, got {resp1.status_code}"

        # With trailing slash
        resp2 = client.get("/api/v1/voices/", headers={"Authorization": "Bearer mock-fb-token"})
        assert resp2.status_code == 200, f"Expected 200 with slash, got {resp2.status_code}"


def test_trailing_slash_invariance_licenses():
    """Verify /api/v1/licenses and /api/v1/licenses/ both return HTTP 200 without 307 redirects."""
    mock_claims = {
        "uid": "fb_slash_tester",
        "email": "slash_tester@whicoustic.xyz",
        "name": "Slash Tester",
    }

    with patch("app.api.v1.auth.verify_firebase_token", return_value=mock_claims):
        # Without trailing slash
        resp1 = client.get("/api/v1/licenses", headers={"Authorization": "Bearer mock-fb-token"})
        assert resp1.status_code == 200, f"Expected 200 without slash, got {resp1.status_code}"

        # With trailing slash
        resp2 = client.get("/api/v1/licenses/", headers={"Authorization": "Bearer mock-fb-token"})
        assert resp2.status_code == 200, f"Expected 200 with slash, got {resp2.status_code}"


def test_verify_stats_route_not_shadowed_by_id():
    """Verify /api/v1/verify/stats and /api/v1/verify/stats/ return stats (200), not 404 (Verification not found)."""
    mock_claims = {
        "uid": "fb_stats_tester",
        "email": "stats_tester@whicoustic.xyz",
        "name": "Stats Tester",
    }

    with patch("app.api.v1.auth.verify_firebase_token", return_value=mock_claims):
        resp1 = client.get("/api/v1/verify/stats", headers={"Authorization": "Bearer mock-fb-token"})
        assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}: {resp1.text}"
        data1 = resp1.json()
        assert "total_verifications" in data1
        assert "watermarks_found" in data1
        assert "success_rate" in data1

        resp2 = client.get("/api/v1/verify/stats/", headers={"Authorization": "Bearer mock-fb-token"})
        assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}: {resp2.text}"
        data2 = resp2.json()
        assert "total_verifications" in data2



# ---------------------------------------------------------------------------
# Tests: Multipart Audio Upload with Firebase ID Token
# ---------------------------------------------------------------------------
def test_voice_upload_with_firebase_token():
    """Verify POST /api/v1/voices/upload accepts multipart form data with Firebase token."""
    mock_claims = {
        "uid": "fb_uploader_99",
        "email": "uploader_99@whicoustic.xyz",
        "name": "Audio Uploader",
    }
    wav_bytes = _generate_wav_bytes(duration_sec=6.0)

    with patch("app.api.v1.auth.verify_firebase_token", return_value=mock_claims), \
         patch("app.api.v1.voices.AudioProcessor.get_audio_info_from_path", return_value={
             "duration": 6.0,
             "sample_rate": 16000,
             "file_size_bytes": len(wav_bytes),
             "quality_score": 0.92,
         }), \
         patch("app.api.v1.voices.voice_training_service.start_training", new_callable=AsyncMock):

        files = {"file": ("test_voice.wav", wav_bytes, "audio/wav")}
        data = {"name": "Test Acoustic Voice", "description": "Verification voice upload"}

        response = client.post(
            "/api/v1/voices/upload",
            files=files,
            data=data,
            headers={"Authorization": "Bearer mock-fb-token-upload"},
        )

        assert response.status_code == 200, f"Upload failed: {response.text}"
        body = response.json()
        assert "voice_id" in body
        assert body["name"] == "Test Acoustic Voice"
        assert body["status"] == "pending"

        # Also test slash route /api/v1/voices/upload/
        response_slash = client.post(
            "/api/v1/voices/upload/",
            files=files,
            data=data,
            headers={"Authorization": "Bearer mock-fb-token-upload"},
        )
        assert response_slash.status_code == 200


def test_voice_upload_mp3_and_m4a_formats():
    """Verify POST /api/v1/voices/upload accepts standard browser audio/mpeg (MP3) and audio/x-m4a (M4A)."""
    mock_claims = {
        "uid": "fb_uploader_mp3",
        "email": "mp3_uploader@whicoustic.xyz",
        "name": "MP3 Uploader",
    }
    dummy_audio = b"\xff\xfb\x90\x00" + b"\x00" * 2000

    with patch("app.api.v1.auth.verify_firebase_token", return_value=mock_claims), \
         patch("app.api.v1.voices.AudioProcessor.get_audio_info_from_path", return_value={
             "duration": 12.5,
             "sample_rate": 44100,
             "file_size_bytes": len(dummy_audio),
             "quality_score": 0.88,
         }), \
         patch("app.api.v1.voices.voice_training_service.start_training", new_callable=AsyncMock):

        # Test audio/mpeg MP3
        files_mp3 = {"file": ("sample_voice.mp3", dummy_audio, "audio/mpeg")}
        data_mp3 = {"name": "MP3 Demo Voice"}
        resp_mp3 = client.post(
            "/api/v1/voices/upload",
            files=files_mp3,
            data=data_mp3,
            headers={"Authorization": "Bearer mock-fb-token-mp3"},
        )
        assert resp_mp3.status_code == 200, f"MP3 upload failed: {resp_mp3.text}"
        assert resp_mp3.json()["status"] == "pending"

        # Test audio/x-m4a M4A
        files_m4a = {"file": ("sample_voice.m4a", dummy_audio, "audio/x-m4a")}
        data_m4a = {"name": "M4A Demo Voice"}
        resp_m4a = client.post(
            "/api/v1/voices/upload",
            files=files_m4a,
            data=data_m4a,
            headers={"Authorization": "Bearer mock-fb-token-m4a"},
        )
        assert resp_m4a.status_code == 200, f"M4A upload failed: {resp_m4a.text}"
        assert resp_m4a.json()["status"] == "pending"


def test_voice_upload_validation_guards():
    """Verify POST /api/v1/voices/upload rejects unsupported extensions and too short audio."""
    mock_claims = {
        "uid": "fb_uploader_guards",
        "email": "guards@whicoustic.xyz",
        "name": "Guards Tester",
    }
    dummy_bytes = b"non_audio_binary_data"

    with patch("app.api.v1.auth.verify_firebase_token", return_value=mock_claims):
        # 1. Unsupported file format (.exe)
        files_invalid = {"file": ("malicious.exe", dummy_bytes, "application/octet-stream")}
        resp_invalid = client.post(
            "/api/v1/voices/upload",
            files=files_invalid,
            data={"name": "Bad File"},
            headers={"Authorization": "Bearer mock-fb-token-guards"},
        )
        assert resp_invalid.status_code == 400
        assert "Unsupported file type" in resp_invalid.json()["detail"]

        # 2. Too short audio (< 1.0 second)
        with patch("app.api.v1.voices.AudioProcessor.get_audio_info_from_path", return_value={
            "duration": 0.4,
            "sample_rate": 16000,
            "file_size_bytes": 100,
            "quality_score": 0.5,
        }):
            files_short = {"file": ("tiny.wav", dummy_bytes, "audio/wav")}
            resp_short = client.post(
                "/api/v1/voices/upload",
                files=files_short,
                data={"name": "Tiny Audio"},
                headers={"Authorization": "Bearer mock-fb-token-guards"},
            )
            assert resp_short.status_code == 400
            assert "too short" in resp_short.json()["detail"]


# ---------------------------------------------------------------------------
# Tests: CORS Preflight & Allowed Origins
# ---------------------------------------------------------------------------
def test_cors_preflight_options():
    """Verify CORS preflight OPTIONS request returns 200 with allowed headers across all production origins."""
    origins = [
        "https://whicoustic.ai",
        "https://app.whicoustic.ai",
        "https://api.whicoustic.xyz",
        "https://whicoustic.onrender.com",
        "http://localhost:5173",
    ]
    for origin in origins:
        response = client.options(
            "/api/v1/voices",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization, content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin
        assert response.headers.get("access-control-allow-credentials") == "true"
        allow_methods = response.headers.get("access-control-allow-methods", "")
        assert "GET" in allow_methods
        assert "POST" in allow_methods
        assert "OPTIONS" in allow_methods


# ---------------------------------------------------------------------------
# Tests: Account Takeover & Hardening Regressions (Milestone 7 Remediation)
# ---------------------------------------------------------------------------
def test_firebase_token_mismatched_uid_account_takeover_rejected():
    """Verify Firebase token with victim's email but attacker's mismatched UID is rejected with 401."""
    db = TestingSessionLocal()
    victim_uid = f"fb_victim_{uuid.uuid4().hex[:8]}"
    victim_email = f"victim_{uuid.uuid4().hex[:6]}@whicoustic.xyz"
    victim_user = User(
        id=str(uuid.uuid4()),
        username=f"victim_{uuid.uuid4().hex[:6]}",
        email=victim_email,
        firebase_uid=victim_uid,
        is_active=True,
    )
    db.add(victim_user)
    db.commit()
    db.refresh(victim_user)

    # Attacker presents valid token with victim's email but attacker's distinct UID
    attacker_uid = f"fb_attacker_{uuid.uuid4().hex[:8]}"
    mock_attacker_claims = {
        "uid": attacker_uid,
        "email": victim_email,
        "name": "Attacker Intruder",
    }

    with patch("app.api.v1.auth.verify_firebase_token", return_value=mock_attacker_claims):
        response = client.get("/api/v1/voices", headers={"Authorization": "Bearer mock-attacker-token"})
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert "Bearer" in response.headers["WWW-Authenticate"]
        assert "already linked" in response.json().get("detail", "").lower()

    # Verify victim's database record was untouched and not claimed by attacker
    db.refresh(victim_user)
    assert victim_user.firebase_uid == victim_uid
    attacker_in_db = db.query(User).filter(User.firebase_uid == attacker_uid).first()
    assert attacker_in_db is None
    db.close()


def test_firebase_token_auto_provisioning_username_collision_recovery():
    """Verify concurrent username collision during auto-provisioning triggers randomized retry and succeeds."""
    db = TestingSessionLocal()
    colliding_name = f"colliding_{uuid.uuid4().hex[:6]}"
    existing_user = User(
        id=str(uuid.uuid4()),
        username=colliding_name,
        email=f"existing_{uuid.uuid4().hex[:6]}@whicoustic.xyz",
        firebase_uid=f"fb_existing_{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(existing_user)
    db.commit()

    new_uid = f"fb_new_{uuid.uuid4().hex[:8]}"
    new_email = f"collision_candidate_{uuid.uuid4().hex[:6]}@whicoustic.xyz"
    mock_claims = {
        "uid": new_uid,
        "email": new_email,
        "name": colliding_name,
    }

    # Simulate race where _ensure_unique_username returns colliding_name, causing IntegrityError on commit
    with patch("app.api.v1.auth.verify_firebase_token", return_value=mock_claims), \
         patch("app.api.v1.auth._ensure_unique_username", return_value=colliding_name):
        response = client.get("/api/v1/voices", headers={"Authorization": "Bearer mock-fb-token-collision"})
        assert response.status_code == 200, f"Expected 200 after collision recovery, got {response.status_code}: {response.text}"
        assert isinstance(response.json(), list)

    new_user_in_db = db.query(User).filter(User.firebase_uid == new_uid).first()
    assert new_user_in_db is not None
    assert new_user_in_db.email == new_email
    assert new_user_in_db.username != colliding_name
    assert new_user_in_db.username.startswith(colliding_name[:40])
    db.close()


def test_firebase_auth_mock_token_production_rejected():
    """Verify verify_firebase_token('mock-token-123') raises HTTP 401 when MOCK_AUTH_ENABLED=False or ENVIRONMENT='production'."""
    from app.core.firebase_auth import verify_firebase_token
    from fastapi import HTTPException

    orig_env = settings.ENVIRONMENT
    orig_mock = settings.MOCK_AUTH_ENABLED

    try:
        # Scenario A: Standard production configuration (ENVIRONMENT='production', MOCK_AUTH_ENABLED=False)
        settings.ENVIRONMENT = "production"
        settings.MOCK_AUTH_ENABLED = False

        resp1 = client.get("/api/v1/voices", headers={"Authorization": "Bearer mock-token-123"})
        assert resp1.status_code == 401, f"Expected 401 in production, got {resp1.status_code}"
        assert "WWW-Authenticate" in resp1.headers
        assert "Bearer" in resp1.headers["WWW-Authenticate"]

        # Direct call to verify_firebase_token must raise 401
        with pytest.raises(HTTPException) as exc_info:
            verify_firebase_token("mock-token-123")
        assert exc_info.value.status_code == 401

        # Scenario B: Misconfiguration defense-in-depth (ENVIRONMENT='production', MOCK_AUTH_ENABLED=True)
        settings.ENVIRONMENT = "production"
        settings.MOCK_AUTH_ENABLED = True

        # Endpoint check must reject
        resp2 = client.get("/api/v1/voices", headers={"Authorization": "Bearer mock-token-123"})
        assert resp2.status_code == 401, f"Expected 401 with MOCK_AUTH_ENABLED=True in production, got {resp2.status_code}"
        assert "WWW-Authenticate" in resp2.headers

        # Core verify_firebase_token must also reject
        with pytest.raises(HTTPException) as exc_info_2:
            verify_firebase_token("mock-token-123")
        assert exc_info_2.value.status_code == 401

        # Scenario C: Development with MOCK_AUTH_ENABLED=False
        settings.ENVIRONMENT = "development"
        settings.MOCK_AUTH_ENABLED = False

        with pytest.raises(HTTPException) as exc_info_3:
            verify_firebase_token("mock-token-123")
        assert exc_info_3.value.status_code == 401

    finally:
        settings.ENVIRONMENT = orig_env
        settings.MOCK_AUTH_ENABLED = orig_mock


def test_firebase_auth_core_verify_token_fallback_on_admin_failure():
    """Verify that verify_firebase_token falls back to google.oauth2.id_token when Firebase Admin fails."""
    from unittest.mock import MagicMock
    from app.core import firebase_auth
    from app.core.firebase_auth import verify_firebase_token

    mock_google_decoded = {
        "sub": "fb_fallback_user_1",
        "email": "fallback_user@whicoustic.xyz",
        "name": "Fallback User",
        "picture": "https://whicoustic.xyz/avatar.png",
    }

    mock_fb_admin = MagicMock()
    mock_fb_auth = MagicMock()
    mock_fb_auth.verify_id_token.side_effect = Exception("Service account mismatch or revoked")

    with patch.object(firebase_auth, "firebase_admin", mock_fb_admin), \
         patch.object(firebase_auth, "fb_auth", mock_fb_auth), \
         patch.object(firebase_auth, "_ensure_firebase_app", return_value=None), \
         patch.object(firebase_auth.google_id_token, "verify_firebase_token", return_value=mock_google_decoded):

        claims = verify_firebase_token("valid-google-public-token-abc")
        assert claims["uid"] == "fb_fallback_user_1"
        assert claims["email"] == "fallback_user@whicoustic.xyz"
        assert claims["name"] == "Fallback User"
        assert claims["picture"] == "https://whicoustic.xyz/avatar.png"
        assert "is_admin" in claims


def test_firebase_auth_core_get_current_user_dependency():
    """Verify app.core.firebase_auth.get_current_user enforces Bearer scheme and returns claims."""
    import asyncio
    from fastapi import HTTPException
    from app.core.firebase_auth import get_current_user as core_get_current_user
    from fastapi.security import HTTPAuthorizationCredentials

    # 1. Missing credentials header -> 401
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(core_get_current_user(None))
    assert exc_info.value.status_code == 401
    assert "WWW-Authenticate" in exc_info.value.headers
    assert "Bearer" in exc_info.value.headers["WWW-Authenticate"]

    # 2. Invalid scheme -> 401
    with pytest.raises(HTTPException) as exc_info_scheme:
        asyncio.run(core_get_current_user(HTTPAuthorizationCredentials(scheme="Basic", credentials="xyz")))
    assert exc_info_scheme.value.status_code == 401

    # 3. Valid Bearer credentials
    mock_claims = {
        "uid": "core_user_1",
        "email": "core@whicoustic.xyz",
        "name": "Core User",
        "is_admin": False,
    }
    with patch("app.core.firebase_auth.verify_firebase_token", return_value=mock_claims):
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-core-1")
        resolved = asyncio.run(core_get_current_user(creds))
        assert resolved["uid"] == "core_user_1"
        assert resolved["email"] == "core@whicoustic.xyz"


def test_voices_list_and_upload_with_google_cert_fallback_token():
    """Verify GET /api/v1/voices/ and POST /api/v1/voices/upload succeed when token verified via Google cert fallback."""
    from unittest.mock import MagicMock
    from app.core import firebase_auth

    mock_google_decoded = {
        "sub": "fb_cert_uploader",
        "email": "cert_uploader@whicoustic.xyz",
        "name": "Cert Uploader",
        "picture": None,
    }
    dummy_wav = b"RIFF" + struct.pack("<I", 44 + 4000) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 16000, 32000, 2, 16) + b"data" + struct.pack("<I", 4000) + (b"\x00\x00" * 2000)

    mock_fb_admin = MagicMock()
    mock_fb_auth = MagicMock()
    mock_fb_auth.verify_id_token.side_effect = Exception("Project mismatch on service account")

    with patch.object(firebase_auth, "firebase_admin", mock_fb_admin), \
         patch.object(firebase_auth, "fb_auth", mock_fb_auth), \
         patch.object(firebase_auth, "_ensure_firebase_app", return_value=None), \
         patch.object(firebase_auth.google_id_token, "verify_firebase_token", return_value=mock_google_decoded), \
         patch("app.api.v1.voices.AudioProcessor.get_audio_info_from_path", return_value={
             "duration": 5.0,
             "sample_rate": 16000,
             "file_size_bytes": len(dummy_wav),
             "quality_score": 0.95,
         }), \
         patch("app.api.v1.voices.voice_training_service.start_training", new_callable=AsyncMock):

        # 1. GET /api/v1/voices/
        resp_get = client.get("/api/v1/voices/", headers={"Authorization": "Bearer google-cert-token-xyz"})
        assert resp_get.status_code == 200, f"Expected 200, got {resp_get.status_code}: {resp_get.text}"
        assert isinstance(resp_get.json(), list)

        # 2. POST /api/v1/voices/upload
        files = {"file": ("demo_cert.wav", dummy_wav, "audio/wav")}
        data = {"name": "Cert Fallback Voice"}
        resp_post = client.post(
            "/api/v1/voices/upload",
            files=files,
            data=data,
            headers={"Authorization": "Bearer google-cert-token-xyz"}
        )
        assert resp_post.status_code == 200, f"Expected 200, got {resp_post.status_code}: {resp_post.text}"
        assert resp_post.json()["name"] == "Cert Fallback Voice"
        assert resp_post.json()["status"] == "pending"


def test_voices_endpoints_reject_invalid_or_missing_tokens():
    """Verify GET and POST voice endpoints reject unauthenticated or malformed requests with 401."""
    dummy_wav = b"RIFF" + struct.pack("<I", 44 + 100) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 16000, 32000, 2, 16) + b"data" + struct.pack("<I", 100) + (b"\x00" * 100)

    # 1. GET /api/v1/voices/ without header
    resp_get_no_token = client.get("/api/v1/voices/")
    assert resp_get_no_token.status_code == 401
    assert "WWW-Authenticate" in resp_get_no_token.headers
    assert "Bearer" in resp_get_no_token.headers["WWW-Authenticate"]

    # 2. GET /api/v1/voices/ with malformed token
    resp_get_bad_token = client.get("/api/v1/voices/", headers={"Authorization": "Bearer totally-invalid-token"})
    assert resp_get_bad_token.status_code == 401
    assert "WWW-Authenticate" in resp_get_bad_token.headers

    # 3. POST /api/v1/voices/upload without header
    resp_post_no_token = client.post(
        "/api/v1/voices/upload",
        files={"file": ("test.wav", dummy_wav, "audio/wav")},
        data={"name": "No Token"}
    )
    assert resp_post_no_token.status_code == 401
    assert "WWW-Authenticate" in resp_post_no_token.headers

    # 4. POST /api/v1/voices/upload with malformed token
    resp_post_bad_token = client.post(
        "/api/v1/voices/upload",
        files={"file": ("test.wav", dummy_wav, "audio/wav")},
        data={"name": "Bad Token"},
        headers={"Authorization": "Bearer invalid.malformed.jwt"}
    )
    assert resp_post_bad_token.status_code == 401
    assert "WWW-Authenticate" in resp_post_bad_token.headers


def test_verify_access_token_endpoint_with_firebase_and_local_tokens():
    """Verify POST /api/v1/auth/verify-token supports Firebase ID tokens, local JWTs, and rejects invalid tokens with 401."""
    # 1. Local JWT token
    local_token = create_access_token(data={"sub": "local_user_77"})
    resp_local = client.post("/api/v1/auth/verify-token", headers={"Authorization": f"Bearer {local_token}"})
    assert resp_local.status_code == 200
    assert resp_local.json()["valid"] is True
    assert resp_local.json()["user_id"] == "local_user_77"

    # 2. Firebase ID token
    mock_fb_claims = {
        "uid": "fb_verified_user_99",
        "email": "verified@whicoustic.xyz",
        "name": "Verified User",
        "is_admin": False,
    }
    with patch("app.api.v1.auth.verify_firebase_token", return_value=mock_fb_claims):
        resp_fb = client.post("/api/v1/auth/verify-token", headers={"Authorization": "Bearer fb-valid-token-99"})
        assert resp_fb.status_code == 200
        assert resp_fb.json()["valid"] is True
        assert resp_fb.json()["user_id"] == "fb_verified_user_99"

    # 3. Invalid token returns 401 with WWW-Authenticate header
    resp_invalid = client.post("/api/v1/auth/verify-token", headers={"Authorization": "Bearer invalid-garbage-token"})
    assert resp_invalid.status_code == 401
    assert "WWW-Authenticate" in resp_invalid.headers
    assert "Bearer" in resp_invalid.headers["WWW-Authenticate"]

    # 4. Missing token returns 401
    resp_missing = client.post("/api/v1/auth/verify-token")
    assert resp_missing.status_code == 401
    assert "WWW-Authenticate" in resp_missing.headers


def test_firebase_token_clock_skew_tolerance():
    """Verify verify_firebase_token passes clock_skew_in_seconds=10 to google verifier."""
    from app.core import firebase_auth
    from unittest.mock import MagicMock

    mock_google_decoded = {
        "sub": "skew_user_1",
        "email": "skew@whicoustic.xyz",
        "name": "Skew User",
    }
    mock_verifier = MagicMock(return_value=mock_google_decoded)

    with patch.object(firebase_auth, "firebase_admin", None), \
         patch.object(firebase_auth.google_id_token, "verify_firebase_token", mock_verifier):

        claims = firebase_auth.verify_firebase_token("token-with-slight-drift")
        assert claims["uid"] == "skew_user_1"
        assert mock_verifier.called
        # Verify clock_skew_in_seconds was passed as 10
        kwargs = mock_verifier.call_args.kwargs
        assert kwargs.get("clock_skew_in_seconds") == 10


def test_empty_or_whitespace_bearer_credentials_returns_401_not_500():
    """Verify empty/whitespace bearer tokens return HTTP 401 with WWW-Authenticate, not 500."""
    from app.api.v1 import auth as v1_auth
    from app.core import firebase_auth
    from fastapi.security import HTTPAuthorizationCredentials

    # 1. API endpoint call with empty Bearer
    resp_empty = client.get("/api/v1/voices/", headers={"Authorization": "Bearer "})
    assert resp_empty.status_code == 401
    assert "WWW-Authenticate" in resp_empty.headers

    # 2. API endpoint call with whitespace Bearer
    resp_ws = client.get("/api/v1/voices/", headers={"Authorization": "Bearer    "})
    assert resp_ws.status_code == 401
    assert "WWW-Authenticate" in resp_ws.headers

    # 3. Direct invocation of v1_auth.get_current_user with credentials=None
    db = next(override_get_db())
    try:
        none_cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")
        with pytest.raises(HTTPException) as exc_info:
            import asyncio
            asyncio.run(v1_auth.get_current_user(none_cred, db))
        assert exc_info.value.status_code == 401
        assert "WWW-Authenticate" in exc_info.value.headers

        # 4. Direct invocation of core firebase_auth.get_current_user with empty credentials
        with pytest.raises(HTTPException) as exc_info_fb:
            asyncio.run(firebase_auth.get_current_user(none_cred))
        assert exc_info_fb.value.status_code == 401
        assert "WWW-Authenticate" in exc_info_fb.value.headers
    finally:
        db.close()


def test_voice_id_trailing_slash_invariance():
    """Verify GET /api/v1/voices/{voice_id} and GET /api/v1/voices/{voice_id}/ both return 200 without 307 redirect."""
    db = next(override_get_db())
    try:
        user = db.query(User).filter(User.email == "demo@whicoustic.com").first()
        if not user:
            user = User(
                username="demo_user_ts",
                email="demo@whicoustic.com",
                hashed_password="pw",
                full_name="Demo User",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        test_voice_id = "voice_ts_test_01"
        voice = db.query(Voice).filter(Voice.id == test_voice_id).first()
        if not voice:
            voice = Voice(
                id=test_voice_id,
                user_id=user.id,
                name="Slash Test Voice",
                status="ready",
                duration=5.0,
                quality_score=0.98,
            )
            db.add(voice)
            db.commit()

        # Both endpoints should return 200 directly (no 307 redirect)
        resp_no_slash = client.get(f"/api/v1/voices/{test_voice_id}", headers={"Authorization": "Bearer mock-token-123"})
        assert resp_no_slash.status_code == 200
        assert resp_no_slash.json()["id"] == test_voice_id

        resp_with_slash = client.get(f"/api/v1/voices/{test_voice_id}/", headers={"Authorization": "Bearer mock-token-123"})
        assert resp_with_slash.status_code == 200
        assert resp_with_slash.json()["id"] == test_voice_id
    finally:
        db.close()


def test_google_auth_request_reset_on_failure():
    """Verify _reset_google_auth_request resets the cached connection pool."""
    from app.core import firebase_auth

    firebase_auth._get_google_auth_request()
    firebase_auth._reset_google_auth_request()
    assert firebase_auth._google_auth_request is None


def test_voice_audio_synthesis_sound_quality_and_amplitude():
    """Verify VoiceProcessor.synthesize_speech produces audible, non-silent audio with no NaNs."""
    import asyncio
    import soundfile as sf
    from app.services.voice_processor import VoiceProcessor
    
    vp = VoiceProcessor()
    
    # Test 1: synthesize with None embedding
    out_path1 = asyncio.run(vp.synthesize_speech(
        text="Testing audio output without embedding",
        voice_id="test_voice_none_emb",
        speaker_embedding=None
    ))
    assert os.path.exists(out_path1), f"Audio file not generated: {out_path1}"
    data1, sr1 = sf.read(out_path1)
    assert len(data1) > 0, "Audio file is empty"
    assert not np.isnan(data1).any(), "Audio data contains NaNs"
    peak1 = float(np.max(np.abs(data1)))
    assert peak1 > 0.5, f"Expected audible peak > 0.5, got {peak1}"
    assert peak1 <= 1.0, f"Peak exceeded clipping threshold: {peak1}"

    # Test 2: synthesize with real vector embedding
    dummy_embedding = [0.15, -0.22, 0.44, 0.08, -0.05]
    out_path2 = asyncio.run(vp.synthesize_speech(
        text="Testing audio output with valid speaker embedding",
        voice_id="test_voice_with_emb",
        speaker_embedding=dummy_embedding
    ))
    assert os.path.exists(out_path2), f"Audio file not generated: {out_path2}"
    data2, sr2 = sf.read(out_path2)
    assert len(data2) > 0, "Audio file is empty"
    assert not np.isnan(data2).any(), "Audio data contains NaNs"
    peak2 = float(np.max(np.abs(data2)))
    assert peak2 > 0.5, f"Expected audible peak > 0.5, got {peak2}"


def test_voice_preview_and_stream_routes_playback():
    """Verify /api/v1/voices/{voice_id}/preview and /stream both return audio without 401."""
    wav_bytes = _generate_wav_bytes(duration_sec=3.0)
    
    # Write a test audio file into data/processed_voices
    processed_dir = Path("data/processed_voices")
    processed_dir.mkdir(parents=True, exist_ok=True)
    test_wav = processed_dir / "voice_preview_test_processed.wav"
    with open(test_wav, "wb") as f:
        f.write(wav_bytes)

    # Insert a dummy voice record into in-memory test DB session
    from app.models.voice import Voice
    db = TestingSessionLocal()
    try:
        existing = db.query(Voice).filter(Voice.id == "voice_preview_test").first()
        if not existing:
            v = Voice(
                id="voice_preview_test",
                user_id="fb_slash_tester",
                name="Preview Test Voice",
                file_path=str(test_wav),
                status="ready",
                duration=3.0,
                sample_rate=16000,
                file_size=len(wav_bytes)
            )
            db.add(v)
            db.commit()
    finally:
        db.close()

    # Stream route (no Authorization header required)
    resp_stream = client.get("/api/v1/voices/voice_preview_test/stream")
    assert resp_stream.status_code in (200, 206), f"Stream failed: {resp_stream.status_code}"
    assert len(resp_stream.content) > 0
    assert resp_stream.headers.get("content-type") == "audio/wav"

    # Preview route (supports unauthenticated player stream with rate limit)
    resp_prev = client.get("/api/v1/voices/voice_preview_test/preview")
    assert resp_prev.status_code in (200, 206), f"Preview failed: {resp_prev.status_code}"
    assert len(resp_prev.content) > 0
    assert resp_prev.headers.get("content-type") == "audio/wav"


def test_tts_download_dual_routes_and_job_sync():
    """Verify /api/v1/tts/download/{job_id} and /job/{job_id}/download dual routes."""
    from app.services.tts_service import tts_service
    
    # Create test synthesized file
    out_dir = Path("data/tts_outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    test_file = out_dir / "test_synth_file.wav"
    wav_bytes = _generate_wav_bytes(duration_sec=2.0)
    with open(test_file, "wb") as f:
        f.write(wav_bytes)

    job_id = "tts_dual_test_123"
    tts_service._jobs[job_id] = {
        "job_id": job_id,
        "user_id": "test_user_tts",
        "output_file": str(test_file),
        "status": "completed",
    }

    # Route 1: /api/v1/tts/download/{job_id}
    resp1 = client.get(f"/api/v1/tts/download/{job_id}")
    assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}"
    assert resp1.headers.get("content-type") == "audio/wav"
    assert len(resp1.content) == len(wav_bytes)

    # Route 2: /api/v1/tts/job/{job_id}/download
    resp2 = client.get(f"/api/v1/tts/job/{job_id}/download")
    assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}"
    assert len(resp2.content) == len(wav_bytes)


# ---------------------------------------------------------------------------
# Standalone Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=======================================================================")
    print("RUNNING MILESTONE 7 AUTH CHAIN TEST SUITE (STANDALONE RUNNER)")
    print("=======================================================================")
    test_missing_bearer_token_returns_401_with_www_authenticate()
    print("  [PASS] test_missing_bearer_token_returns_401_with_www_authenticate")
    test_non_bearer_scheme_returns_401()
    print("  [PASS] test_non_bearer_scheme_returns_401")
    test_malformed_token_returns_401()
    print("  [PASS] test_malformed_token_returns_401")
    test_expired_local_jwt_returns_401()
    print("  [PASS] test_expired_local_jwt_returns_401")
    test_dev_mock_token_success()
    print("  [PASS] test_dev_mock_token_success")
    test_local_hs256_jwt_verification()
    print("  [PASS] test_local_hs256_jwt_verification")
    test_disabled_user_account_returns_403_forbidden()
    print("  [PASS] test_disabled_user_account_returns_403_forbidden")
    test_firebase_token_auto_provisions_new_user()
    print("  [PASS] test_firebase_token_auto_provisions_new_user")
    test_firebase_token_links_existing_user_by_email()
    print("  [PASS] test_firebase_token_links_existing_user_by_email")
    test_trailing_slash_invariance_voices()
    print("  [PASS] test_trailing_slash_invariance_voices")
    test_trailing_slash_invariance_licenses()
    print("  [PASS] test_trailing_slash_invariance_licenses")
    test_voice_upload_with_firebase_token()
    print("  [PASS] test_voice_upload_with_firebase_token")
    test_cors_preflight_options()
    print("  [PASS] test_cors_preflight_options (all production & staging origins)")
    test_firebase_token_mismatched_uid_account_takeover_rejected()
    print("  [PASS] test_firebase_token_mismatched_uid_account_takeover_rejected")
    test_firebase_token_auto_provisioning_username_collision_recovery()
    print("  [PASS] test_firebase_token_auto_provisioning_username_collision_recovery")
    test_firebase_auth_mock_token_production_rejected()
    print("  [PASS] test_firebase_auth_mock_token_production_rejected")
    test_firebase_auth_core_verify_token_fallback_on_admin_failure()
    print("  [PASS] test_firebase_auth_core_verify_token_fallback_on_admin_failure")
    test_firebase_auth_core_get_current_user_dependency()
    print("  [PASS] test_firebase_auth_core_get_current_user_dependency")
    test_voices_list_and_upload_with_google_cert_fallback_token()
    print("  [PASS] test_voices_list_and_upload_with_google_cert_fallback_token")
    test_voices_endpoints_reject_invalid_or_missing_tokens()
    print("  [PASS] test_voices_endpoints_reject_invalid_or_missing_tokens")
    test_verify_access_token_endpoint_with_firebase_and_local_tokens()
    print("  [PASS] test_verify_access_token_endpoint_with_firebase_and_local_tokens")
    test_firebase_token_clock_skew_tolerance()
    print("  [PASS] test_firebase_token_clock_skew_tolerance")
    test_empty_or_whitespace_bearer_credentials_returns_401_not_500()
    print("  [PASS] test_empty_or_whitespace_bearer_credentials_returns_401_not_500")
    test_voice_id_trailing_slash_invariance()
    print("  [PASS] test_voice_id_trailing_slash_invariance")
    test_google_auth_request_reset_on_failure()
    print("  [PASS] test_google_auth_request_reset_on_failure")
    print("=======================================================================")
    print("ALL 25 VERIFICATION TESTS PASSED (100%)!")
    print("=======================================================================")
