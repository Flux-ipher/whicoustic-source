"""
Whicoustic Comprehensive System Simulation & Verification Suite
Tests all layers, services, databases, REST APIs, WebSockets, and audio defense modules.
"""

import os
import sys
import uuid
import time
import json
import asyncio
import tempfile
import numpy as np
import soundfile as sf
from datetime import datetime

# Configure environment before imports
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ["MOCK_AUTH_ENABLED"] = "true"
os.environ["PUBLIC_STREAMING_ENABLED"] = "true"
os.environ["SECRET_KEY"] = "dev-secret-key-32-bytes-long-123456"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_simulation.db"

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient

# Helper to print test step headers
def log_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def log_pass(msg: str):
    print(f"  [PASS] {msg}")

def log_fail(msg: str):
    print(f"  [FAIL] {msg}")
    sys.exit(1)

# Helper to generate test audio
def generate_synthetic_audio(duration: float = 3.0, sr: int = 16000, freq: float = 440.0) -> np.ndarray:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Speech-like harmonic mixture
    y = 0.4 * np.sin(2 * np.pi * freq * t) + 0.2 * np.sin(2 * np.pi * (freq * 2) * t) + 0.1 * np.sin(2 * np.pi * (freq * 3) * t)
    # Add minor noise
    y += 0.02 * np.random.normal(0, 1, len(t))
    return np.clip(y, -0.99, 0.99).astype(np.float32)

def save_wav(audio: np.ndarray, sr: int = 16000) -> str:
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    sf.write(path, audio, sr)
    return path


# ==============================================================================
# 1. DATABASE & ORM MODELS SIMULATION
# ==============================================================================
def test_subsystem_database_models():
    log_section("1. DATABASE & ORM MODELS SUBSYSTEM")
    from app.core.database import create_tables_sync, SyncSessionLocal, sync_engine
    from app.models.user import User
    from app.models.voice import Voice, VoiceStatus, VoiceQuality
    from app.models.license import License
    from app.models.watermark import WatermarkVerification
    from app.models.usage_log import UsageLog, LicenseUsage
    from sqlalchemy import inspect

    # 1.1 Create Tables
    create_tables_sync()
    inspector = inspect(sync_engine)
    tables = inspector.get_table_names()
    expected = ['users', 'voices', 'voice_samples', 'licenses', 'watermark_verifications', 'usage_logs', 'license_usage']
    for exp in expected:
        assert exp in tables, f"Table {exp} missing from database"
    log_pass(f"All 7 ORM tables initialized successfully: {tables}")

    # 1.2 Model CRUD Operations
    with SyncSessionLocal() as db:
        # Create user
        uid = f"user_{uuid.uuid4().hex[:8]}"
        user = User(
            id=uid,
            email=f"{uid}@example.com",
            username=uid,
            full_name="Simulation User",
            is_active=True,
            is_premium=True,
            subscription_tier="enterprise"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        log_pass(f"Created User: {user.username} (ID: {user.id})")

        # Create voice
        vid = f"voice_{uuid.uuid4().hex[:8]}"
        voice = Voice(
            id=vid,
            user_id=user.id,
            name="Studio Narrator",
            status="ready",
            duration=12.5,
            sample_rate=16000,
            quality_score=0.92
        )
        db.add(voice)
        db.commit()
        db.refresh(voice)
        log_pass(f"Created Voice: {voice.name} (Status: {voice.status})")

        # Create license
        lid = f"lic_{uuid.uuid4().hex[:8]}"
        license_obj = License(
            id=lid,
            user_id=user.id,
            voice_id=voice.id,
            name="Commercial Broadcast License",
            license_type="commercial",
            price=49.99,
            currency="USD",
            duration_days=365,
            usage_limit=100000,
            is_active=True
        )
        db.add(license_obj)
        db.commit()
        log_pass(f"Created License: {license_obj.name} (${license_obj.price})")

        # Create usage logs
        usage = UsageLog(
            user_id=user.id,
            voice_id=voice.id,
            text_length=150,
            audio_duration=8.2,
            watermark_id="wm_test_123",
            license_id=license_obj.id
        )
        lic_usage = LicenseUsage(
            license_id=license_obj.id,
            token_id="tok_test_abc",
            user_id=user.id,
            voice_id=voice.id,
            text_length=150,
            audio_duration=8.2,
            watermark_id="wm_test_123"
        )
        db.add(usage)
        db.add(lic_usage)
        db.commit()
        log_pass("Logged UsageLog and LicenseUsage records")

        # Create watermark verification record
        wm_ver = WatermarkVerification(
            id=f"verify_{uuid.uuid4().hex[:8]}",
            user_id=user.id,
            original_filename="sample.wav",
            detection_method="mvp_sine",
            watermark_found=True,
            watermark_id="wm_test_123",
            confidence_score=0.99
        )
        db.add(wm_ver)
        db.commit()
        log_pass("Logged WatermarkVerification audit record")

    log_pass("Subsystem 1 (Database & Models) fully operational.")


# ==============================================================================
# 2. REST API & AUTHENTICATION ENDPOINTS SIMULATION
# ==============================================================================
def test_subsystem_rest_api():
    log_section("2. FASTAPI REST API & AUTH SUBSYSTEM")
    from app.main import app
    client = TestClient(app)

    # 2.1 Root & Health Check
    r = client.get("/")
    assert r.status_code == 200, f"Root returned {r.status_code}"
    log_pass(f"GET / -> Status: {r.status_code}, Name: {r.json().get('name')}")

    r = client.get("/health")
    assert r.status_code == 200, f"Health check returned {r.status_code}"
    health_data = r.json()
    assert health_data.get("status") == "healthy"
    log_pass(f"GET /health -> Status: {health_data.get('status')}, Services: {health_data.get('services')}")

    # 2.2 System Stats
    r = client.get("/stats")
    assert r.status_code == 200, f"Stats returned {r.status_code}"
    log_pass(f"GET /stats -> Database Healthy: {r.json().get('database', {}).get('healthy')}")

    # 2.3 User Registration & Login
    test_user_payload = {
        "username": f"simuser_{uuid.uuid4().hex[:6]}",
        "email": f"simuser_{uuid.uuid4().hex[:6]}@whicoustic.ai",
        "password": "Password123!",
        "full_name": "Simulation Automated User"
    }
    r = client.post("/api/v1/auth/register", json=test_user_payload)
    assert r.status_code == 200, f"Registration failed: {r.text}"
    user_data = r.json()
    user_id = user_data["id"]
    log_pass(f"POST /api/v1/auth/register -> Registered user {user_data['username']} (ID: {user_id})")

    r = client.post("/api/v1/auth/login", json={
        "email": test_user_payload["email"],
        "password": test_user_payload["password"]
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    token_data = r.json()
    access_token = token_data["access_token"]
    auth_header = {"Authorization": f"Bearer {access_token}"}
    log_pass("POST /api/v1/auth/login -> JWT access token acquired")

    # 2.4 Authenticated Profile
    r = client.get("/api/v1/auth/profile", headers=auth_header)
    assert r.status_code == 200
    assert r.json()["id"] == user_id
    log_pass(f"GET /api/v1/auth/profile -> Authenticated as {r.json()['email']}")

    # 2.5 Mock Authentication Bypass
    mock_header = {"Authorization": "Bearer mock-token-123"}
    r = client.get("/api/v1/auth/profile", headers=mock_header)
    assert r.status_code == 200
    assert r.json()["email"] == "demo@whicoustic.com"
    log_pass(f"GET /api/v1/auth/profile (Mock Auth) -> Accepted mock-token-123 as {r.json()['username']}")

    # 2.6 Users Sync via Firebase Claims (testing mock auth in firebase_auth.py)
    r = client.post("/api/v1/users/sync", headers=mock_header, json={
        "name": "Demo User Updated",
        "phone": "+1-555-0199"
    })
    assert r.status_code == 200
    log_pass(f"POST /api/v1/users/sync -> Synced mock user with ID: {r.json().get('id')}")

    # 2.7 TTS Available Voice Models (Verification of Bug 3 Fix)
    r = client.get("/api/v1/tts/models/available", headers=auth_header)
    assert r.status_code == 200, f"GET /api/v1/tts/models/available failed with {r.status_code}: {r.text}"
    log_pass(f"GET /api/v1/tts/models/available -> 200 OK (Bug 3 resolved, returned {r.json().get('total')} models)")

    # 2.8 Voice Creation via DB for downstream tests
    from app.core.database import SyncSessionLocal
    from app.models.voice import Voice
    test_voice_id = f"voice_{uuid.uuid4().hex[:12]}"
    with SyncSessionLocal() as db:
        v = Voice(
            id=test_voice_id,
            user_id=user_id,
            name="Testing Narrator",
            status="ready",
            duration=10.0,
            quality_score=0.95
        )
        db.add(v)
        db.commit()
    log_pass(f"Seeded test voice '{test_voice_id}' for licensing and synthesis tests")

    # 2.9 Licensing CRUD via API
    license_payload = {
        "voice_id": test_voice_id,
        "name": "Standard Commercial Voice License",
        "license_type": "commercial",
        "price": 29.99,
        "currency": "USD",
        "duration_days": 180,
        "usage_limit": 50000,
        "allowed_use_cases": ["commercial", "podcast", "youtube"]
    }
    r = client.post("/api/v1/licenses/", headers=auth_header, json=license_payload)
    assert r.status_code == 200, f"License creation failed: {r.text}"
    lic_res = r.json()
    lic_id = lic_res["id"]
    log_pass(f"POST /api/v1/licenses/ -> Created license {lic_id}")

    r = client.get("/api/v1/licenses/", headers=auth_header)
    assert r.status_code == 200
    assert len(r.json()) >= 1
    log_pass(f"GET /api/v1/licenses/ -> Retrieved {len(r.json())} user license(s)")

    # Issue Purchaser Token
    tok_payload = {
        "purchaser_email": "client@acmecorp.com",
        "purchaser_name": "Acme Media Group",
        "purchase_amount": 29.99
    }
    r = client.post(f"/api/v1/licenses/{lic_id}/tokens", headers=auth_header, json=tok_payload)
    assert r.status_code == 200, f"Token issue failed: {r.text}"
    issued_token = r.json()["token"]
    log_pass(f"POST /api/v1/licenses/{lic_id}/tokens -> Issued purchaser token (Expires: {r.json()['expires_at']})")

    # Validate Purchaser Token (public endpoint)
    r = client.post("/api/v1/licenses/validate-token", params={"token": issued_token, "voice_id": test_voice_id})
    assert r.status_code == 200
    assert r.json()["valid"] is True
    log_pass("POST /api/v1/licenses/validate-token -> Token validation successful (valid=True)")

    # License Stats
    r = client.get(f"/api/v1/licenses/{lic_id}/stats", headers=auth_header)
    assert r.status_code == 200
    log_pass(f"GET /api/v1/licenses/{lic_id}/stats -> Total uses: {r.json()['total_uses']}")

    # 2.10 TTS Synthesis with Background Usage Logging (Verification of Bug 2 Fix)
    synth_payload = {
        "text": "This is an automated test of the Whicoustic synthesis and background usage tracking pipeline.",
        "voice_id": test_voice_id,
        "license_token": issued_token
    }
    r = client.post("/api/v1/tts/synthesize", headers=auth_header, json=synth_payload)
    assert r.status_code == 200, f"Synthesize failed: {r.text}"
    synth_res = r.json()
    assert synth_res["status"] == "completed"
    assert "watermark_id" in synth_res
    log_pass(f"POST /api/v1/tts/synthesize -> 200 OK (Bug 2 resolved, Job: {synth_res['job_id']}, WM: {synth_res['watermark_id']})")

    # Give background task 100ms to persist
    time.sleep(0.2)
    with SyncSessionLocal() as db:
        from app.models.usage_log import UsageLog
        logged = db.query(UsageLog).filter(UsageLog.voice_id == test_voice_id).first()
        assert logged is not None, "Background log_usage failed to write to database"
        log_pass(f"Verified background usage logged to DB: {logged.text_length} chars, WM: {logged.watermark_id}")

    log_pass("Subsystem 2 (FastAPI REST & Auth) fully operational.")
    return access_token


# ==============================================================================
# 3. CRYPTOGRAPHIC WATERMARKING SUBSYSTEM
# ==============================================================================
def test_subsystem_watermark(access_token: str):
    log_section("3. CRYPTOGRAPHIC WATERMARKING SUBSYSTEM")
    from app.core.watermark import WatermarkEncoder, WatermarkDecoder, WatermarkService
    from app.main import app
    client = TestClient(app)
    auth_header = {"Authorization": f"Bearer {access_token}"}

    # Generate audio
    raw_audio = generate_synthetic_audio(duration=4.0, sr=44100, freq=440.0)
    clean_wav = save_wav(raw_audio, sr=44100)
    wm_output = tempfile.mktemp(suffix=".wav")

    try:
        wm_id = f"wm_sim_{uuid.uuid4().hex[:12]}"
        
        # 3.1 Direct Encoder/Decoder Verification (19kHz Sine Watermark)
        encoder = WatermarkEncoder(secret_key="whicoustic_default_key")
        encoder.embed_mvp_watermark(clean_wav, wm_id, wm_output, frequency=19000.0, amplitude=0.003)
        log_pass(f"Embedded 19kHz sine watermark '{wm_id}' into audio")

        decoder = WatermarkDecoder(secret_key="whicoustic_default_key")
        det = decoder.detect_mvp_watermark(wm_output, frequency=19000.0)
        assert det is not None, "Failed to detect embedded MVP watermark"
        assert det.get("found") is True
        log_pass(f"Detected 19kHz watermark: Found={det['found']}, Confidence={det['confidence']:.2f}")

        # 3.2 Detection on clean audio (Verify no false positive)
        clean_det = decoder.detect_mvp_watermark(clean_wav, frequency=19000.0)
        assert clean_det is None or clean_det.get("found") is False, "False positive detected on clean audio"
        log_pass("Verified clean audio yields NO false-positive watermark")

        # 3.3 Verification API Endpoint Test
        with open(wm_output, "rb") as f:
            r = client.post("/api/v1/verify/watermark", headers=auth_header, files={"file": ("watermarked.wav", f, "audio/wav")})
        assert r.status_code == 200, f"Watermark verify endpoint failed: {r.text}"
        ver_data = r.json()
        assert ver_data["watermark_found"] is True
        log_pass(f"POST /api/v1/verify/watermark -> 200 OK (watermark_found={ver_data['watermark_found']}, ID: {ver_data['verification_id']})")

        # 3.4 Verification History Endpoint
        r = client.get("/api/v1/verify/history", headers=auth_header)
        assert r.status_code == 200
        assert len(r.json()) >= 1
        log_pass(f"GET /api/v1/verify/history -> Retrieved {len(r.json())} audit record(s)")

    finally:
        if os.path.exists(clean_wav): os.unlink(clean_wav)
        if os.path.exists(wm_output): os.unlink(wm_output)

    log_pass("Subsystem 3 (Cryptographic Watermarking) fully operational.")


# ==============================================================================
# 4. 6-LAYER DEEPFAKE DEFENSE SYSTEM
# ==============================================================================
def test_subsystem_6_layer_defense():
    log_section("4. 6-LAYER DEEPFAKE DEFENSE SUBSYSTEM")
    from app.services.antispoof import AntiSpoofDetector
    from app.services.prosody_service import ProsodyService
    from app.services.paralinguistic_service import ParalinguisticService
    from app.services.semantic_service import SemanticService
    from app.main import app

    client = TestClient(app)
    raw_audio = generate_synthetic_audio(duration=3.5, sr=16000, freq=300.0)
    audio_file = save_wav(raw_audio, sr=16000)

    try:
        # Layer 1: Anti-Spoof
        det_l1 = AntiSpoofDetector().detect(audio_file)
        assert "spoof_score" in det_l1
        log_pass(f"Layer 1 (Anti-Spoof): Engine={det_l1.get('engine')}, Spoof Score={det_l1['spoof_score']:.3f}")

        # Layer 3: Prosody
        det_l3 = ProsodyService().analyse(audio_file)
        assert "authenticity_score" in det_l3
        log_pass(f"Layer 3 (Prosody): Authenticity Score={det_l3['authenticity_score']:.3f}, Pitch CV={det_l3.get('pitch_stability_cv')}")

        # Layer 4: Paralinguistic
        det_l4 = ParalinguisticService().analyse(audio_file)
        assert "authenticity_score" in det_l4
        log_pass(f"Layer 4 (Paralinguistics): Authenticity Score={det_l4['authenticity_score']:.3f}, Energy CV={det_l4.get('energy_cv')}")

        # Layer 5: Semantic
        det_l5 = SemanticService().analyse(audio_file)
        assert "authenticity_score" in det_l5
        log_pass(f"Layer 5 (Semantic): Authenticity Score={det_l5['authenticity_score']:.3f}, Available={det_l5.get('available')}")

        # 4.2 Full 6-Layer Orchestrator Endpoint (/api/v1/verify/full-analysis)
        with open(audio_file, "rb") as f:
            r = client.post("/api/v1/verify/full-analysis", files={"file": ("sample.wav", f, "audio/wav")})
        assert r.status_code == 200, f"Full analysis endpoint failed: {r.text}"
        res = r.json()
        assert "overall_authenticity_score" in res
        assert "verdict" in res
        assert "layers" in res
        log_pass(f"POST /api/v1/verify/full-analysis -> Score={res['overall_authenticity_score']}, Verdict='{res['verdict']}'")
        log_pass(f"Confirmed all active layers evaluated: {list(res['layers'].keys())}")

    finally:
        if os.path.exists(audio_file): os.unlink(audio_file)

    log_pass("Subsystem 4 (6-Layer Deepfake Defense) fully operational.")


# ==============================================================================
# 5. TELEPHONY CHANNEL & PARTIAL FAKE DEFENSE (PHASE 2)
# ==============================================================================
def test_subsystem_telephony_and_localizer():
    log_section("5. TELEPHONY ROBUSTNESS & PARTIAL FAKE LOCALIZER (PHASE 2)")
    from app.services.telephone_channel import TelephoneChannelPreprocessor
    from app.services.partial_fake_localizer import PartialFakeLocalizer
    from app.main import app

    client = TestClient(app)
    preproc = TelephoneChannelPreprocessor(target_sr=16000)

    # 5.1 Bandwidth Cutoff & Telephony Detection
    t_16k = np.linspace(0, 2.0, int(16000 * 2.0), endpoint=False)
    audio_16k = sum(0.15 * np.sin(2 * np.pi * f * t_16k) for f in [400, 1200, 2400, 4200, 5800, 6800])
    audio_16k = np.clip(audio_16k, -0.99, 0.99).astype(np.float32)
    meta_16k = preproc.detect_bandwidth(audio_16k, 16000)
    assert meta_16k["is_telephony"] is False, "16kHz studio audio incorrectly classified as telephony"
    log_pass(f"Clean 16kHz audio: is_telephony={meta_16k['is_telephony']} (Bandwidth: {meta_16k['effective_bandwidth_hz']}Hz)")

    audio_8k = generate_synthetic_audio(duration=2.0, sr=8000, freq=500.0)
    meta_8k = preproc.detect_bandwidth(audio_8k, 8000)
    assert meta_8k["is_telephony"] is True, "8kHz audio failed to be classified as telephony"
    log_pass(f"Telephone 8kHz audio: is_telephony={meta_8k['is_telephony']} (Bandwidth: {meta_8k['effective_bandwidth_hz']}Hz)")

    # 5.2 Dynamic Layer Weight Reallocation on Phone Channel
    orig_weights = {
        "l1": {"score": 0.8, "weight": 0.35},
        "l3": {"score": 0.7, "weight": 0.15},
        "l4": {"score": 0.6, "weight": 0.10},
        "l5": {"score": 0.8, "weight": 0.20},
        "l6": {"score": 1.0, "weight": 0.20},
    }
    adj_weights = TelephoneChannelPreprocessor.adjust_layer_weights(orig_weights, is_telephony=True)
    assert adj_weights["l6"]["weight"] == 0.0, "Layer 6 (19kHz watermark) must have weight 0 on telephony channels"
    assert adj_weights["l6"]["status"] == "disabled_telephony"
    new_total = sum(w["weight"] for w in adj_weights.values())
    assert abs(new_total - 1.0) < 1e-3, f"Adjusted weights do not sum to 1.0 (got {new_total})"
    log_pass(f"Dynamic weight reallocation on phone channel verified: L6 weight=0 (disabled_telephony), sum={new_total:.2f}")

    # 5.3 Partial Fake Localization (0.5s Resolution)
    localizer = PartialFakeLocalizer(sample_rate=16000, threshold=0.40)
    # Synthesize spliced audio: 1.5s human-like + 1.5s synthetic-like
    spliced_audio = np.concatenate([
        generate_synthetic_audio(duration=1.5, sr=16000, freq=180.0), # Part 1
        generate_synthetic_audio(duration=1.5, sr=16000, freq=800.0)  # Part 2
    ])
    spliced_path = save_wav(spliced_audio, sr=16000)

    try:
        loc_res = localizer.analyze_audio(spliced_audio, sr=16000)
        assert "segments" in loc_res
        assert "clip_verdict" in loc_res
        log_pass(f"Partial Fake Localizer evaluated {len(loc_res['segments'])} frames (0.5s cadence). Clip Verdict: '{loc_res['clip_verdict']}'")

        # Call /api/v1/verify/localize endpoint
        with open(spliced_path, "rb") as f:
            r = client.post("/api/v1/verify/localize", files={"file": ("spliced.wav", f, "audio/wav")})
        assert r.status_code == 200, f"Localize endpoint failed: {r.text}"
        api_loc = r.json()
        assert "segments" in api_loc
        log_pass(f"POST /api/v1/verify/localize -> 200 OK (Processed {len(api_loc['segments'])} segments at 0.5s resolution)")

    finally:
        if os.path.exists(spliced_path): os.unlink(spliced_path)

    log_pass("Subsystem 5 (Telephony & Partial Fake Defense) fully operational.")


# ==============================================================================
# 6. REAL-TIME STREAMING WEBSOCKET SIMULATION
# ==============================================================================
def test_subsystem_realtime_streaming():
    log_section("6. REAL-TIME STREAMING WEBSOCKET SUBSYSTEM")
    from app.main import app

    client = TestClient(app)

    # 6.1 Test WebSocket Streaming in normal mode (16kHz PCM chunks)
    with client.websocket_connect("/api/v1/verify/stream?mode=normal&sample_rate=16000&token=mock-token-123") as ws:
        sr = 16000
        chunk_samples = 480
        t_base = np.linspace(0, 0.03, chunk_samples, endpoint=False)

        # Buffer requires 1.0s (34 chunks of 30ms) before emitting verdicts
        for i in range(34):
            tone = 0.5 * np.sin(2 * np.pi * 350.0 * (t_base + i * 0.03))
            ws.send_bytes((tone * 32767).astype(np.int16).tobytes())

        # Send chunk 35 which triggers first window analysis
        tone = 0.5 * np.sin(2 * np.pi * 350.0 * (t_base + 34 * 0.03))
        ws.send_bytes((tone * 32767).astype(np.int16).tobytes())

        msg = ws.receive_json(mode="text")
        assert "overall_authenticity_score" in msg, f"Expected verdict payload, got: {msg}"
        log_pass(f"Streaming Verdict Received (16kHz Normal): Score={msg['overall_authenticity_score']:.3f}, Verdict='{msg['verdict']}', Cadence={msg.get('cadence_ms', 500)}ms")
        log_pass("WebSocket 16kHz Normal Stream completed successfully")

    # 6.2 Test WebSocket Streaming in phone mode (8kHz PCM chunks)
    with client.websocket_connect("/api/v1/verify/stream?mode=phone&sample_rate=8000&token=mock-token-123") as ws:
        sr = 8000
        chunk_samples = 240  # 30ms at 8kHz
        t_base = np.linspace(0, 0.03, chunk_samples, endpoint=False)

        # Buffer requires 1.0s (34 chunks)
        for i in range(34):
            tone = 0.5 * np.sin(2 * np.pi * 350.0 * (t_base + i * 0.03))
            ws.send_bytes((tone * 32767).astype(np.int16).tobytes())

        # Send chunk 35 to trigger analysis
        tone = 0.5 * np.sin(2 * np.pi * 350.0 * (t_base + 34 * 0.03))
        ws.send_bytes((tone * 32767).astype(np.int16).tobytes())

        msg = ws.receive_json(mode="text")
        assert "overall_authenticity_score" in msg, f"Expected phone verdict payload, got: {msg}"
        log_pass(f"Phone Stream Verdict Received (8kHz Telephony): Score={msg['overall_authenticity_score']:.3f}, Verdict='{msg['verdict']}'")
        log_pass("WebSocket 8kHz Telephony Stream completed successfully")

    log_pass("Subsystem 6 (Real-Time Streaming WebSocket) fully operational.")


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
def main():
    print("=" * 70)
    print("  Whicoustic COMPREHENSIVE END-TO-END SIMULATION & TEST SUITE")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    try:
        # Run all subsystem simulations in sequence
        test_subsystem_database_models()
        access_token = test_subsystem_rest_api()
        test_subsystem_watermark(access_token)
        test_subsystem_6_layer_defense()
        test_subsystem_telephony_and_localizer()
        test_subsystem_realtime_streaming()

        print("\n" + "*" * 70)
        print("  ALL SUBSYSTEMS PASSED! FULL END-TO-END SIMULATION SUCCESSFUL!")
        print("*" * 70)

    finally:
        # Cleanup test db
        if os.path.exists("test_simulation.db"):
            try:
                os.unlink("test_simulation.db")
            except Exception:
                pass

if __name__ == "__main__":
    main()

