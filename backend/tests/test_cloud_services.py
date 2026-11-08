"""
Comprehensive Verification Suite for Milestone 3:
Backend Cloud Services, Database, Storage, and Rate Limiting.

Tests:
1. Supabase PostgreSQL configuration & resilient automatic SQLite fallback.
2. Google Drive Storage Adapter with automatic local fallback (upload, download, stream, metadata).
3. Audio streaming route GET /api/v1/voices/{voice_id}/stream with HTTP range request support.
4. Render Starter plan deployment configuration (backend/render.yaml and backend/requirements-render.txt).
5. Firebase Auth token verification with dev mock fallback (mock-token-123).
6. Token Bucket & Leaky Token Bucket rate limiters and TTL Memory Cache.
7. Endpoint rate limiting integration.
"""

import os
import sys
import time
import tempfile
import struct
import wave
from pathlib import Path
from typing import Generator
import yaml

# Set environment before any imports
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ["MOCK_AUTH_ENABLED"] = "true"
os.environ["PUBLIC_STREAMING_ENABLED"] = "true"
os.environ["SECRET_KEY"] = "dev-secret-key-32-bytes-long-123456"

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

settings.ENVIRONMENT = "development"
settings.MOCK_AUTH_ENABLED = True
from app.core.database import (
    Base,
    get_db,
    db_manager,
    init_engines,
    _resolve_target_urls,
    SQLITE_ASYNC_URL,
)
from app.models.user import User
from app.models.voice import Voice
from app.api.v1.voices import router as voices_router
from app.api.v1.tts import router as tts_router
from app.services.google_drive_storage import (
    GoogleDriveStorageService,
    get_google_drive_storage,
)
from app.core.firebase_auth import verify_firebase_token
from app.core.rate_limit import (
    TokenBucketRateLimiter,
    LeakyBucketRateLimiter,
    MemoryCache,
    synthesis_limiter,
    streaming_limiter,
    cloning_limiter,
)


def _generate_test_wav(duration_sec: float = 1.0, sample_rate: int = 16000) -> str:
    """Generate a clean synthetic sine-wave WAV file on disk for storage and streaming tests."""
    scratch_dir = Path("D:/Main/.scratch")
    scratch_dir.mkdir(parents=True, exist_ok=True)
    temp_wav = scratch_dir / f"test_audio_{int(time.time() * 1000)}.wav"

    total_samples = int(duration_sec * sample_rate)
    with wave.open(str(temp_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        # Generate 440 Hz tone
        samples = []
        for i in range(total_samples):
            val = int(32767.0 * 0.5 * (1.0 if (i // 18) % 2 == 0 else -1.0))
            samples.append(struct.pack("<h", val))
        wf.writeframes(b"".join(samples))

    return str(temp_wav)


def _build_test_app():
    """Create test FastAPI application with in-memory database and routes."""
    app = FastAPI(title="Whicoustic Cloud Services Test")
    app.include_router(voices_router, prefix="/api/v1")
    app.include_router(tts_router, prefix="/api/v1")

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def _get_test_db() -> Generator:
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    return app, TestingSession


# ==============================================================================
# 1. Supabase PostgreSQL & Resilient Automatic SQLite Fallback Tests
# ==============================================================================
def test_supabase_config_and_resilient_fallback():
    """Verify Supabase settings exist and fallback to SQLite vcaas_dev2.db occurs without crashing."""
    # Verify settings fields
    assert hasattr(settings, "SUPABASE_URL"), "SUPABASE_URL setting must exist"
    assert hasattr(settings, "SUPABASE_KEY"), "SUPABASE_KEY setting must exist"
    assert hasattr(settings, "SUPABASE_SERVICE_ROLE_KEY"), "SUPABASE_SERVICE_ROLE_KEY setting must exist"
    assert hasattr(settings, "SUPABASE_DB_URL"), "SUPABASE_DB_URL setting must exist"

    # Health check on initialized engine
    assert db_manager.health_check() is True, "Database manager health check should pass"
    info = db_manager.get_connection_info()
    assert "sqlite" in info["drivername"].lower(), f"Expected sqlite driver, got {info['drivername']}"

    # Test URL resolver behavior
    orig_supabase = settings.SUPABASE_URL
    orig_db_url = settings.SUPABASE_DB_URL
    try:
        object.__setattr__(settings, "SUPABASE_DB_URL", "postgresql://user:pass@db.example.com:5432/whicoustic")
        async_url, sync_url = _resolve_target_urls()
        assert "postgresql+asyncpg" in async_url
        assert sync_url.startswith("postgresql://")

        # Simulate fallback on unresolvable host
        object.__setattr__(settings, "SUPABASE_DB_URL", "postgresql://invalid:pwd@127.0.0.1:59999/whicoustic")
        a_eng, s_eng, db_type = init_engines()
        assert db_type == "sqlite", "Invalid PostgreSQL host must automatically fall back to SQLite"
    finally:
        object.__setattr__(settings, "SUPABASE_URL", orig_supabase)
        object.__setattr__(settings, "SUPABASE_DB_URL", orig_db_url)


# ==============================================================================
# 2. Google Drive Storage Adapter & Fallback Tests
# ==============================================================================
def test_google_drive_storage_adapter_and_fallback():
    """Verify GoogleDriveStorageService handles upload, download, streaming, and metadata with fallback."""
    wav_path = _generate_test_wav(duration_sec=0.5)
    file_size = os.path.getsize(wav_path)
    assert file_size > 0, "Generated test WAV must be non-empty"

    storage = GoogleDriveStorageService(folder_id=None)  # Forces local storage fallback
    assert storage.is_drive_active is False, "Adapter without folder_id should operate in fallback mode"

    import asyncio

    async def _run_storage_tests():
        # 1. Upload
        upload_res = await storage.upload_file(wav_path, file_name="sample_voice.wav", mime_type="audio/wav")
        assert upload_res["success"] is True, f"Upload failed: {upload_res}"
        file_id = upload_res["file_id"]
        assert file_id.startswith("local_"), "Fallback upload should return a local file_id"
        assert upload_res["file_size"] == file_size

        # 2. Metadata
        meta_res = await storage.get_file_metadata(file_id)
        assert meta_res["success"] is True
        assert meta_res["size"] == file_size
        assert meta_res["storage_type"] == "local"

        # 3. Stream
        chunks = []
        async for chunk in storage.get_file_stream(file_id, chunk_size=1024):
            chunks.append(chunk)
        streamed_bytes = b"".join(chunks)
        assert len(streamed_bytes) == file_size, f"Streamed {len(streamed_bytes)} bytes, expected {file_size}"

        # 4. Download
        dest_download = Path("D:/Main/.scratch") / "downloaded_voice.wav"
        if dest_download.exists():
            dest_download.unlink()
        download_ok = await storage.download_file(file_id, str(dest_download))
        assert download_ok is True
        assert dest_download.exists()
        assert dest_download.stat().st_size == file_size

    asyncio.run(_run_storage_tests())


# ==============================================================================
# 3. Audio Streaming Route (HTTP Range Requests) Tests
# ==============================================================================
def test_audio_streaming_route_with_range_requests():
    """Verify GET /api/v1/voices/{voice_id}/stream supports 200 full stream and 206 range requests."""
    app, SessionLocal = _build_test_app()
    client = TestClient(app)

    wav_path = _generate_test_wav(duration_sec=1.0)
    file_size = os.path.getsize(wav_path)

    # Seed user and voice in db
    with SessionLocal() as db:
        user = User(
            id="user_stream_test",
            email="streamer@whicoustic.ai",
            username="streamer_test",
            full_name="Audio Streamer",
        )
        db.add(user)
        voice = Voice(
            id="voice_stream_101",
            user_id=user.id,
            name="Stream Test Voice",
            file_path=wav_path,
            status="ready",
            duration=1.0,
            file_size=file_size,
        )
        db.add(voice)
        db.commit()

    # 1. Full stream request (No Range header) -> 200 OK
    resp_full = client.get("/api/v1/voices/voice_stream_101/stream")
    assert resp_full.status_code == 200, f"Expected 200, got {resp_full.status_code}: {resp_full.text}"
    assert resp_full.headers.get("Accept-Ranges") == "bytes"
    assert int(resp_full.headers.get("Content-Length")) == file_size
    assert len(resp_full.content) == file_size

    # 2. Byte Range request -> 206 Partial Content (bytes=0-99 -> 100 bytes)
    resp_range_1 = client.get(
        "/api/v1/voices/voice_stream_101/stream",
        headers={"Range": "bytes=0-99"}
    )
    assert resp_range_1.status_code == 206, f"Expected 206, got {resp_range_1.status_code}"
    assert resp_range_1.headers.get("Content-Range") == f"bytes 0-99/{file_size}"
    assert resp_range_1.headers.get("Content-Length") == "100"
    assert len(resp_range_1.content) == 100

    # 3. Tail Range request -> bytes=100-299 -> 200 bytes
    resp_range_2 = client.get(
        "/api/v1/voices/voice_stream_101/stream",
        headers={"Range": "bytes=100-299"}
    )
    assert resp_range_2.status_code == 206
    assert resp_range_2.headers.get("Content-Range") == f"bytes 100-299/{file_size}"
    assert len(resp_range_2.content) == 200

    # 4. Out of bounds range -> 416 Range Not Satisfiable
    resp_invalid = client.get(
        "/api/v1/voices/voice_stream_101/stream",
        headers={"Range": f"bytes={file_size + 100}-{file_size + 200}"}
    )
    assert resp_invalid.status_code == 416

    # 5. Non-existent voice -> 404
    resp_404 = client.get("/api/v1/voices/voice_non_existent/stream")
    assert resp_404.status_code == 404


# ==============================================================================
# 4. Render Deployment Configuration ($7 Starter Plan, 2 GB RAM)
# ==============================================================================
def test_render_starter_configuration():
    """Verify render.yaml and requirements-render.txt conform to Render Starter tier specifications."""
    render_yaml_path = Path(backend_dir) / "render.yaml"
    req_render_path = Path(backend_dir) / "requirements-render.txt"

    assert render_yaml_path.exists(), "backend/render.yaml must exist"
    assert req_render_path.exists(), "backend/requirements-render.txt must exist"

    with open(render_yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "services" in data, "render.yaml must define services"
    web_service = data["services"][0]
    assert web_service["type"] == "web"
    assert web_service["plan"] == "starter", f"Expected 'plan: starter' ($7/mo, 2GB RAM), got {web_service.get('plan')}"
    assert "pip install -r requirements-render.txt" in web_service["buildCommand"]
    assert "uvicorn app.main:app" in web_service["startCommand"]

    # Check requirements-render.txt packages
    req_content = req_render_path.read_text(encoding="utf-8")
    assert "asyncpg" in req_content
    assert "psycopg2-binary" in req_content
    assert "google-api-python-client" in req_content
    assert "google-auth" in req_content
    assert "google-auth-httplib2" in req_content


# ==============================================================================
# 5. Firebase Auth Verification & Dev Mock Fallback
# ==============================================================================
def test_firebase_auth_token_and_mock_fallback():
    """Verify Firebase Auth token verification with dev mock fallback (mock-token-123)."""
    # 1. Dev mock token
    mock_claims = verify_firebase_token("mock-token-123")
    assert mock_claims["uid"] == "demo-user-123"
    assert mock_claims["email"] == "demo@whicoustic.com"
    assert mock_claims["is_admin"] is True

    # 2. Missing token raises 401
    try:
        verify_firebase_token("")
        assert False, "Empty token must raise 401"
    except HTTPException as e:
        assert e.status_code == 401

    # 3. Invalid token without Firebase Admin active raises 500 or 401
    try:
        verify_firebase_token("invalid-token-xyz")
        assert False, "Invalid token must not succeed"
    except HTTPException as e:
        assert e.status_code in (401, 500)


# ==============================================================================
# 6. Advanced Rate Limiting (Token Bucket, Leaky Bucket) & Memory Cache
# ==============================================================================
def test_rate_limiting_algorithms_and_memory_cache():
    """Verify TokenBucketRateLimiter, LeakyBucketRateLimiter, and MemoryCache logic."""
    # 1. Token Bucket
    tb = TokenBucketRateLimiter(capacity=3.0, refill_rate=1.0)
    client_k = "client_alpha"

    # Consume all 3 initial tokens
    assert tb.acquire(client_k, tokens=1.0) is True
    assert tb.acquire(client_k, tokens=1.0) is True
    assert tb.acquire(client_k, tokens=1.0) is True
    # 4th request must be rejected
    assert tb.acquire(client_k, tokens=1.0) is False
    assert tb.get_wait_time(client_k, tokens=1.0) > 0.0

    # Reset
    tb.reset(client_k)
    assert tb.acquire(client_k, tokens=1.0) is True

    # 2. Leaky Bucket
    lb = LeakyBucketRateLimiter(capacity=2.0, leak_rate=1.0)
    client_b = "client_beta"

    assert lb.acquire(client_b, amount=1.0) is True
    assert lb.acquire(client_b, amount=1.0) is True
    # 3rd request exceeds capacity 2.0 -> rejected
    assert lb.acquire(client_b, amount=1.0) is False

    # 3. Memory Cache
    cache = MemoryCache(default_ttl=0.3)
    cache.set("item_1", {"audio": "stream_url"}, ttl=0.2)
    assert cache.has("item_1") is True
    assert cache.get("item_1") == {"audio": "stream_url"}
    assert cache.size() == 1

    # Wait for expiration
    time.sleep(0.25)
    assert cache.get("item_1") is None
    assert cache.has("item_1") is False
    assert cache.size() == 0


# ==============================================================================
# 7. Endpoint Rate Limiting Protection Integration
# ==============================================================================
def test_endpoint_rate_limiting_enforcement():
    """Verify endpoints enforce HTTP 429 when rate limiters are exhausted."""
    app, SessionLocal = _build_test_app()
    client = TestClient(app)

    wav_path = _generate_test_wav(duration_sec=0.5)
    file_size = os.path.getsize(wav_path)

    with SessionLocal() as db:
        user = User(
            id="user_rate_test",
            email="rate_test@whicoustic.ai",
            username="rate_user",
        )
        db.add(user)
        voice = Voice(
            id="voice_rate_test",
            user_id=user.id,
            name="Rate Test Voice",
            file_path=wav_path,
            status="ready",
            duration=0.5,
            file_size=file_size,
        )
        db.add(voice)
        db.commit()

    # 1. Test streaming endpoint rate limiting (Leaky Bucket)
    client_ip = "203.0.113.195"
    streaming_limiter.reset(client_ip)
    # Set water level at capacity with future timestamp (+60s) to prevent leak during dispatch latency
    streaming_limiter._buckets[client_ip] = (streaming_limiter.capacity, time.time() + 60.0)

    resp = client.get(
        "/api/v1/voices/voice_rate_test/stream",
        headers={"X-Forwarded-For": client_ip}
    )
    assert resp.status_code == 429, f"Expected 429, got {resp.status_code}: {resp.text}"
    assert "rate limit exceeded" in resp.json()["detail"].lower()
    assert "Retry-After" in resp.headers

    # Reset limiter for that client and verify it succeeds
    streaming_limiter.reset(client_ip)
    resp_ok = client.get(
        "/api/v1/voices/voice_rate_test/stream",
        headers={"X-Forwarded-For": client_ip}
    )
    assert resp_ok.status_code == 200

    # 2. Test synthesis endpoint rate limiting (Token Bucket)
    synthesis_limiter.reset(client_ip)
    # Exhaust all tokens in bucket with future timestamp (+60s) to prevent refill during dispatch latency
    synthesis_limiter._buckets[client_ip] = (0.0, time.time() + 60.0)

    # Must provide Authorization header to test rate limit on authenticated endpoint
    resp_synth = client.post(
        "/api/v1/tts/synthesize",
        headers={
            "X-Forwarded-For": client_ip,
            "Authorization": "Bearer mock-token-123",
        },
        json={"voice_id": "voice_rate_test", "text": "Hello world"}
    )
    assert resp_synth.status_code == 429, f"Expected 429, got {resp_synth.status_code}: {resp_synth.text}"
    assert "rate limit exceeded" in resp_synth.json()["detail"].lower()
    assert "Retry-After" in resp_synth.headers

    # Reset synthesis limiter
    synthesis_limiter.reset(client_ip)

    # 3. Test cloning endpoint rate limiting (Token Bucket)
    cloning_limiter.reset(client_ip)
    cloning_limiter._buckets[client_ip] = (0.0, time.time() + 60.0)

    resp_clone = client.post(
        "/api/v1/tts/clone",
        headers={
            "X-Forwarded-For": client_ip,
            "Authorization": "Bearer mock-token-123",
        },
        data={"text": "Test clone rate limiting"},
        files={"reference": ("sample.wav", b"RIFF" + b"\x00" * 100, "audio/wav")}
    )
    assert resp_clone.status_code == 429, f"Expected 429, got {resp_clone.status_code}: {resp_clone.text}"
    assert "voice cloning rate limit exceeded" in resp_clone.json()["detail"].lower()
    assert "Retry-After" in resp_clone.headers

    # Reset cloning limiter
    cloning_limiter.reset(client_ip)


if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING MILESTONE 3 BACKEND CLOUD SERVICES & RATE LIMITING TEST SUITE")
    print("=" * 70)

    test_supabase_config_and_resilient_fallback()
    print("PASS: [1/7] Supabase PostgreSQL configuration & resilient SQLite fallback")

    test_google_drive_storage_adapter_and_fallback()
    print("PASS: [2/7] Google Drive storage adapter & local storage fallback")

    test_audio_streaming_route_with_range_requests()
    print("PASS: [3/7] Audio streaming route with HTTP range requests (200 & 206)")

    test_render_starter_configuration()
    print("PASS: [4/7] Render Starter deployment configuration ($7/mo, 2 GB RAM)")

    test_firebase_auth_token_and_mock_fallback()
    print("PASS: [5/7] Firebase Auth ID token verification & dev mock fallback")

    test_rate_limiting_algorithms_and_memory_cache()
    print("PASS: [6/7] Token Bucket, Leaky Bucket algorithms & TTL Memory Cache")

    test_endpoint_rate_limiting_enforcement()
    print("PASS: [7/7] Endpoint rate limiting protection (HTTP 429)")

    print("=" * 70)
    print("ALL 7 CLOUD SERVICE VERIFICATION SUITES PASSED (100% SUCCESS)!")
    print("=" * 70)
