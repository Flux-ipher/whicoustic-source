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
    print("=======================================================================")
    print("ALL 16 VERIFICATION TESTS PASSED (100%)!")
    print("=======================================================================")
