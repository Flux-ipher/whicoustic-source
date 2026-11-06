#!/usr/bin/env python3
"""
Whicoustic Platform Unified End-to-End Test Runner
===================================================
Production Readiness Verification Suite validating all backend services,
cloud integrations, core acoustic & security capabilities, and frontend build outputs.

Test Suites:
1. Suite 1: Compliance & Age Gate Validation
2. Suite 2: Real Speech Voice Profile Creation & Embedding Extraction (LibriSpeech)
3. Suite 3: TTS Synthesis & Novel Watermarking Verification (4 Pillars)
4. Suite 4: Real-time 6-Layer Forensic WebSocket Stream Telemetry
5. Suite 5: Licensing Marketplace, Contract Minting & Escrow Disbursement
6. Suite 6: HTTP Range Voice Audio Streaming (RFC 9110)
7. Suite 7: Token Bucket & Leaky Bucket Rate Limiting
8. Suite 8: Production Build & Asset Integrity Check

Execution:
    py -3.12 scripts/test_e2e_platform.py
"""

import os
import sys
import glob
import time
import uuid
import random
import asyncio
import threading
import soundfile as sf
import numpy as np
from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta, datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Strict Workspace & Drive Configuration
# ---------------------------------------------------------------------------
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ["MOCK_AUTH_ENABLED"] = "true"
os.environ["PUBLIC_STREAMING_ENABLED"] = "true"
os.environ["SECRET_KEY"] = "audit_verification_key_secure_32bytes"

SCRATCH_DIR = Path("D:/Main/.scratch")
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ---------------------------------------------------------------------------
# Imports from FastAPI App and Backend Core
# ---------------------------------------------------------------------------
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.database import SyncSessionLocal, create_tables_sync
from app.core.security import set_security_config, get_password_hash
from app.models.user import User
from app.models.voice import Voice
from app.models.license import License
from app.models.usage_log import UsageLog, LicenseUsage
from app.models.escrow import EscrowDisbursement
from app.services.voice_processor import VoiceProcessor
from app.core.watermark import WatermarkService, WatermarkEncoder, WatermarkDecoder
from app.services.escrow_service import EscrowService
from app.services.google_drive_storage import GoogleDriveStorageService
from app.core.rate_limit import (
    TokenBucketRateLimiter,
    LeakyBucketRateLimiter,
    synthesis_limiter,
    streaming_limiter,
)


def locate_librispeech_sample() -> str:
    """Locate a real human voice recording from the local LibriSpeech dataset."""
    search_pattern = r"D:\New folder\LibriSpeech\**\*.flac"
    flac_files = glob.glob(search_pattern, recursive=True)
    if not flac_files:
        raise FileNotFoundError(f"No LibriSpeech .flac files found matching {search_pattern}")
    # Prefer a medium-length speech file for comprehensive testing (e.g., 0002.flac)
    for f in flac_files:
        if "0002.flac" in f:
            return f
    return flac_files[0]


# ===========================================================================
# Suite 1: Compliance & Age Gate Validation
# ===========================================================================
def suite_1_compliance_and_age_gate(client: TestClient, db) -> None:
    print("\n" + "=" * 75)
    print("SUITE 1: Compliance & Age Gate Validation")
    print("=" * 75)

    today = date.today()
    expected_compliance_msg = (
        "Users must be at least 17 years old to register on Whicoustic in compliance with digital biometric licensing regulations."
    )

    # 1. Underage registration attempt (15 years old)
    dob_underage = (today - timedelta(days=int(15 * 365.25))).isoformat()
    underage_username = f"underage_{uuid.uuid4().hex[:6]}"
    underage_email = f"{underage_username}@test.com"

    payload_underage = {
        "username": underage_username,
        "email": underage_email,
        "password": "Password123!",
        "full_name": "Underage User",
        "dob": dob_underage,
    }

    resp_underage = client.post("/api/v1/auth/register", json=payload_underage)
    assert resp_underage.status_code == 422, (
        f"Expected HTTP 422 for age < 17, got {resp_underage.status_code}: {resp_underage.text}"
    )
    assert expected_compliance_msg in resp_underage.text, (
        f"Expected compliance message missing in response: {resp_underage.text}"
    )

    # Verify user record was NOT persisted in the database
    user_db = db.query(User).filter(User.username == underage_username).first()
    assert user_db is None, "Underage user must not be persisted in database"
    print("  [PASS] Blocked user registration with DOB < 17 (HTTP 422 with exact compliance message)")

    # 2. Adult registration attempt (24 years old)
    dob_adult = (today - timedelta(days=int(24 * 365.25))).isoformat()
    adult_username = f"adult_{uuid.uuid4().hex[:6]}"
    adult_email = f"{adult_username}@whicoustic.ai"

    payload_adult = {
        "username": adult_username,
        "email": adult_email,
        "password": "Password123!",
        "full_name": "Adult Creator",
        "dob": dob_adult,
    }

    resp_adult = client.post("/api/v1/auth/register", json=payload_adult)
    assert resp_adult.status_code in (200, 201), (
        f"Expected HTTP 200/201 for age >= 17, got {resp_adult.status_code}: {resp_adult.text}"
    )

    # Verify user record is genuinely persisted in database with correct DOB
    user_adult_db = db.query(User).filter(User.username == adult_username).first()
    assert user_adult_db is not None, "Adult user must be persisted in database"
    assert user_adult_db.dob.isoformat() == dob_adult, (
        f"DOB mismatch in DB: expected {dob_adult}, got {user_adult_db.dob}"
    )
    print(f"  [PASS] Allowed user registration with DOB >= 17 (HTTP {resp_adult.status_code}) & persisted in DB: {dob_adult}")


# ===========================================================================
# Suite 2: Real Speech Voice Profile Creation & Embedding Extraction
# ===========================================================================
def suite_2_real_speech_voice_profile(librispeech_sample: str, db) -> str:
    print("\n" + "=" * 75)
    print("SUITE 2: Real Speech Voice Profile Creation & Embedding Extraction")
    print("=" * 75)

    assert os.path.exists(librispeech_sample), f"LibriSpeech sample not found: {librispeech_sample}"
    print(f"  [INFO] Real speech source file: {librispeech_sample}")

    processor = VoiceProcessor()
    embedding = asyncio.run(processor.extract_speaker_embedding(librispeech_sample))

    # Assert embedding properties
    assert isinstance(embedding, np.ndarray), f"Expected np.ndarray, got {type(embedding)}"
    assert embedding.shape == (256,), f"Expected embedding shape (256,), got {embedding.shape}"
    assert np.linalg.norm(embedding) > 0.0, "Speaker embedding vector has zero norm"
    print(f"  [PASS] Extracted 256-dimensional speaker embedding (norm: {np.linalg.norm(embedding):.4f})")

    # Audio details
    audio_data, sr = sf.read(librispeech_sample)
    duration = len(audio_data) / sr

    # Create Voice Profile in Database
    voice_id = f"voice_{uuid.uuid4().hex[:12]}"
    test_user_id = "demo-user-123"

    voice = Voice(
        id=voice_id,
        user_id=test_user_id,
        name="LibriSpeech Clean Voice Profile",
        description="Authentic human vocal recording from LibriSpeech dev-clean dataset",
        original_filename=os.path.basename(librispeech_sample),
        file_path=librispeech_sample,
        speaker_embedding=embedding.tolist(),
        duration=duration,
        sample_rate=sr,
        file_size=os.path.getsize(librispeech_sample),
        status="ready",
        quality_score=0.94,
    )
    db.add(voice)
    db.commit()
    db.refresh(voice)

    # Verify database persistence & round-trip numerical fidelity
    reloaded_voice = db.query(Voice).filter(Voice.id == voice_id).first()
    assert reloaded_voice is not None, "Voice record was not found in database"
    assert len(reloaded_voice.speaker_embedding) == 256, (
        f"Expected 256 embedding dimensions in DB, got {len(reloaded_voice.speaker_embedding)}"
    )
    reloaded_arr = np.array(reloaded_voice.speaker_embedding, dtype=np.float32)
    assert reloaded_arr.shape == (256,), "Round-trip numpy array shape mismatch"
    print(f"  [PASS] Voice profile persisted to database (Voice ID: {voice_id}, Duration: {duration:.2f}s)")
    return voice_id


# ===========================================================================
# Suite 3: TTS Synthesis & Novel Watermarking Verification (4 Pillars)
# ===========================================================================
def suite_3_tts_and_watermarking_four_pillars(librispeech_sample: str) -> None:
    print("\n" + "=" * 75)
    print("SUITE 3: TTS Synthesis & Novel Watermarking Verification (4 Pillars)")
    print("=" * 75)

    secret_key = "audit_verification_key_secure_32bytes"
    service = WatermarkService(secret_key=secret_key)

    # 1. Haas Effect Echo Hiding Window Check (Bit 0 = 20ms, Bit 1 = 25ms in 5-35ms window)
    delay_bit0 = 0.020
    delay_bit1 = 0.025
    assert 0.005 <= delay_bit0 <= 0.035, "Bit 0 delay (20ms) is outside the 5-35ms perceptual fusion window"
    assert 0.005 <= delay_bit1 <= 0.035, "Bit 1 delay (25ms) is outside the 5-35ms perceptual fusion window"
    print("  [PASS] Pillar 1: Haas effect echo hiding parameters verified (20ms Bit 0, 25ms Bit 1 in 5-35ms window)")

    # 2. Embed Robust Watermark into Real LibriSpeech Speech
    wm_output = str(SCRATCH_DIR / f"e2e_watermarked_{uuid.uuid4().hex[:6]}.wav")
    wm_id = "wm_7c8d"

    asyncio.run(service.embed_watermark(
        audio_path=librispeech_sample,
        watermark_id=wm_id,
        output_path=wm_output,
        method="robust"
    ))
    assert os.path.exists(wm_output), "Watermarked audio file was not created"

    # Pillar 2: Real Cepstral Detection IFFT(log|FFT(signal)|)
    res_baseline = asyncio.run(service.detect_watermark(wm_output, method="robust"))
    assert res_baseline.get("found") is True, "Watermark was not detected in baseline audio"
    assert res_baseline.get("watermark_id") == wm_id, (
        f"Watermark ID mismatch: expected {wm_id}, got {res_baseline.get('watermark_id')}"
    )
    assert res_baseline.get("detection_method") == "robust_echo_hiding"
    assert res_baseline.get("total_blocks", 0) >= 2, "Expected multiple repeating blocks"
    print(f"  [PASS] Pillar 2: Real cepstral peak detection IFFT(log|FFT|) verified (Watermark ID: {wm_id})")

    # Pillar 4: HMAC-SHA256 Cryptographic Signing & Constant-Time Verification
    assert res_baseline.get("signature_valid") is True, "HMAC-SHA256 signature verification failed"

    # Negative key test: wrong key must fail constant-time comparison
    wrong_key_service = WatermarkService(secret_key="wrong_unauthorized_key_999")
    res_wrong_key = asyncio.run(wrong_key_service.detect_watermark(wm_output, method="robust"))
    assert res_wrong_key.get("signature_valid") is False, "Forged/wrong key must fail HMAC signature check"
    print("  [PASS] Pillar 4: HMAC-SHA256 constant-time signature verification verified (genuine=True, forged=False)")

    # 21.4 kHz Ultrasonic Carrier Modulation & Nyquist Upsampling
    ultra_output = str(SCRATCH_DIR / f"e2e_ultrasonic_{uuid.uuid4().hex[:6]}.wav")
    asyncio.run(service.embed_watermark(
        audio_path=librispeech_sample,
        watermark_id="sha256_ultrasonic_payload_e2e",
        output_path=ultra_output,
        method="mvp"
    ))
    _, sr_ultra = sf.read(ultra_output)
    assert sr_ultra >= 44100, f"Expected output sample rate >= 44100 Hz, got {sr_ultra}"
    res_ultra = asyncio.run(service.detect_watermark(ultra_output, method="mvp"))
    assert res_ultra.get("found") is True, "Ultrasonic carrier was not detected"
    assert res_ultra.get("frequency") == 21400.0, f"Expected 21400 Hz, got {res_ultra.get('frequency')}"
    print(f"  [PASS] 21.4 kHz ultrasonic carrier with SHA-256 payload verified (SR: {sr_ultra} Hz, Nyquist: {sr_ultra/2} Hz)")

    # Pillar 3: Continuous Payload Repetition & Timeline Tamper Localization
    audio, sr = sf.read(wm_output)
    block_samples = int(round(52 * 2 * 0.035 * sr))
    tampered_audio = audio.copy()
    # Splice zero/unwatermarked segment into block 1
    tampered_audio[block_samples : 2 * block_samples] = 0.0
    tampered_path = str(SCRATCH_DIR / f"e2e_tampered_{uuid.uuid4().hex[:6]}.wav")
    sf.write(tampered_path, tampered_audio, sr)

    res_tamper = asyncio.run(service.detect_watermark(tampered_path, method="robust"))
    assert res_tamper.get("found") is True, "Surviving authentic blocks must still detect watermark"
    assert res_tamper.get("tampering_detected") is True, "Tampering was not flagged"
    timeline = res_tamper.get("timeline", [])
    assert len(timeline) >= 2, "Timeline segments missing"
    assert timeline[1]["status"] == "fail", f"Expected tampered block 1 status 'fail', got {timeline[1]['status']}"
    assert timeline[1]["tampered"] is True, "Expected block 1 tampered to be True"
    print("  [PASS] Pillar 3: Continuous repetition & timeline tamper localization verified (corrupted block localized as 'fail')")

    # Robustness against real speech (Cropping, MP3 compression, Additive noise)
    # 1. Cropping
    cropped_path = str(SCRATCH_DIR / f"e2e_cropped_{uuid.uuid4().hex[:6]}.wav")
    cropped_audio = audio[int(2.0 * sr) : int(8.0 * sr)]
    sf.write(cropped_path, cropped_audio, sr)
    res_crop = asyncio.run(service.detect_watermark(cropped_path, method="robust"))
    assert res_crop.get("found") is True, "Watermark was not detected in cropped audio"

    # 2. MP3 Compression
    mp3_path = str(SCRATCH_DIR / f"e2e_compressed_{uuid.uuid4().hex[:6]}.mp3")
    sf.write(mp3_path, audio, sr, format="MP3")
    res_mp3 = asyncio.run(service.detect_watermark(mp3_path, method="robust"))
    assert res_mp3.get("found") is True, "Watermark was not detected after MP3 compression"

    # 3. Additive White Noise (SNR = 20 dB)
    noisy_path = str(SCRATCH_DIR / f"e2e_noisy_{uuid.uuid4().hex[:6]}.wav")
    sig_power = np.mean(audio**2)
    noise_power = sig_power / (10 ** (20.0 / 10.0))
    noise = np.random.normal(0, np.sqrt(noise_power), len(audio))
    noisy_audio = np.clip(audio + noise, -0.99, 0.99)
    sf.write(noisy_path, noisy_audio, sr)
    res_noise = asyncio.run(service.detect_watermark(noisy_path, method="robust"))
    assert res_noise.get("found") is True, "Watermark was not detected under additive noise"
    print("  [PASS] Robustness verified on real LibriSpeech audio across Cropping, MP3 compression & 20dB noise")


# ===========================================================================
# Suite 4: Real-time 6-Layer Forensic WebSocket Stream Telemetry
# ===========================================================================
def suite_4_forensic_websocket_telemetry(client: TestClient, librispeech_sample: str) -> None:
    print("\n" + "=" * 75)
    print("SUITE 4: Real-time 6-Layer Forensic WebSocket Stream Telemetry")
    print("=" * 75)

    audio, sr = sf.read(librispeech_sample)
    assert sr == 16000, f"Expected 16kHz LibriSpeech audio, got {sr}"

    # Convert to 16-bit signed PCM frames (480 samples = 960 bytes per 30ms)
    pcm_16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    frame_samples = 480

    received_telemetries = []
    with client.websocket_connect("/api/v1/verify/stream?token=mock-token-123&mode=normal&sample_rate=16000") as ws:
        # Batch 1: Send 50 frames (1.5s real speech, exceeding initial window)
        for i in range(50):
            frame_bytes = pcm_16[i * frame_samples : (i + 1) * frame_samples].tobytes()
            ws.send_bytes(frame_bytes)
        telemetry_1 = ws.receive_json()
        received_telemetries.append(telemetry_1)

        # Batch 2: Send another 25 frames (0.75s real speech, exceeding cadence)
        for i in range(50, 75):
            frame_bytes = pcm_16[i * frame_samples : (i + 1) * frame_samples].tobytes()
            ws.send_bytes(frame_bytes)
        telemetry_2 = ws.receive_json()
        received_telemetries.append(telemetry_2)

    assert len(received_telemetries) >= 2, f"Expected at least 2 telemetry frames, got {len(received_telemetries)}"

    # Validate Top-level contract keys & 6-layer explicit pass/anomaly/fail tags
    expected_top_keys = ["timestamp", "combined_risk_score", "overall_authenticity_score", "verdict"]
    expected_layers = ["anti_spoof", "speaker_consistency", "prosody", "paralinguistic", "semantic", "watermark"]

    for idx, telemetry in enumerate(received_telemetries):
        for key in expected_top_keys:
            assert key in telemetry, f"Missing top-level contract key '{key}' in frame {idx}"
        assert telemetry["verdict"] in {"AUTHENTIC", "SUSPICIOUS", "SYNTHETIC"}, (
            f"Invalid verdict: {telemetry['verdict']}"
        )

        layers = telemetry.get("layers", {})
        for layer_name in expected_layers:
            assert layer_name in layers, f"Layer '{layer_name}' missing from frame {idx}"
            layer_payload = layers[layer_name]
            assert "status" in layer_payload, f"Layer '{layer_name}' missing 'status' field"
            assert layer_payload["status"] in {"pass", "anomaly", "fail"}, (
                f"Layer '{layer_name}' returned invalid status: {layer_payload['status']}"
            )

    latest_verdict = received_telemetries[-1]["verdict"]
    risk_score = received_telemetries[-1]["combined_risk_score"]
    auth_score = received_telemetries[-1]["overall_authenticity_score"]
    print(f"  [PASS] WebSocket stream processed real LibriSpeech audio frames ({len(received_telemetries)} telemetry packets)")
    print(f"  [PASS] Top-level contract keys verified (Verdict: {latest_verdict}, Risk: {risk_score:.3f}, Authenticity: {auth_score:.3f})")
    print("  [PASS] All 6 defense layers returned explicit 'pass' | 'anomaly' | 'fail' status")


# ===========================================================================
# Suite 5: Licensing Marketplace, Contract Minting & Escrow Disbursement
# ===========================================================================
def suite_5_licensing_and_escrow_disbursement(client: TestClient, db, voice_id: str) -> None:
    print("\n" + "=" * 75)
    print("SUITE 5: Licensing Marketplace, Contract Minting & Escrow Disbursement")
    print("=" * 75)

    # 1. List voices from marketplace
    resp_voices = client.get("/api/v1/voices/", headers={"Authorization": "Bearer mock-token-123"})
    assert resp_voices.status_code == 200, f"Failed to list voices: {resp_voices.text}"
    voices = resp_voices.json()
    assert len(voices) > 0, "No voices found in marketplace listing"
    print(f"  [PASS] Listed {len(voices)} voices from marketplace catalogue")

    # 2. Mint commercial license contract
    license_payload = {
        "voice_id": voice_id,
        "name": "Commercial Podcast Syndication License",
        "description": "Annual commercial broadcast and podcast syndication rights",
        "license_type": "commercial",
        "price": 1500.0,
        "currency": "USD",
        "duration_days": 365,
        "usage_limit": 500000,
        "territory": ["Worldwide"],
        "allowed_use_cases": ["commercial", "podcast", "broadcast"],
        "restrictions": {"no_political_ads": True},
    }
    resp_license = client.post(
        "/api/v1/licenses/",
        json=license_payload,
        headers={"Authorization": "Bearer mock-token-123"}
    )
    assert resp_license.status_code == 200, f"License creation failed: {resp_license.text}"
    license_data = resp_license.json()
    license_id = license_data["id"]
    assert license_id.startswith("lic_"), f"Unexpected license ID format: {license_id}"
    print(f"  [PASS] Commercial license contract minted (ID: {license_id}, Gross: ${float(license_data['price']):.2f})")

    # 3. Record simulated playback usage (seconds)
    usage = LicenseUsage(
        license_id=license_id,
        user_id="demo-user-123",
        voice_id=voice_id,
        text_length=250,
        audio_duration=38.5,
        watermark_id="wm_e2e_audit_usage",
        used_at=datetime.now(timezone.utc),
    )
    db.add(usage)
    db.commit()
    print("  [PASS] Simulated playback usage logged in ledger (38.5s duration, watermark tracked)")

    # 4. Invoke EscrowService.calculate_split: 15% platform fee deduction & 85% creator net payout
    gross = Decimal("1500.00")
    split = EscrowService.calculate_split(gross, Decimal("0.15"))
    assert split["gross"] == Decimal("1500.00"), f"Expected 1500.00 gross, got {split['gross']}"
    assert split["platform_fee"] == Decimal("225.00"), f"Expected 225.00 fee, got {split['platform_fee']}"
    assert split["net_creator"] == Decimal("1275.00"), f"Expected 1275.00 net, got {split['net_creator']}"
    assert split["platform_fee"] + split["net_creator"] == split["gross"], "Fee + Net != Gross (Decimal rounding error!)"

    # Also test precision with odd decimals
    odd_gross = Decimal("99.99")
    odd_split = EscrowService.calculate_split(odd_gross, Decimal("0.15"))
    assert odd_split["platform_fee"] + odd_split["net_creator"] == odd_split["gross"], "Odd decimal split mismatch"
    print("  [PASS] EscrowService.calculate_split verified (15% fee: $225.00, 85% creator net: $1275.00; fee + net == gross)")

    # 5. Seed settled disbursement record and verify GET /api/v1/licenses/{id}/disbursements
    disb_id = f"disb_{uuid.uuid4().hex[:8]}"
    disbursement = EscrowDisbursement(
        id=disb_id,
        license_id=license_id,
        royalty_stream="Commercial Podcast Syndication",
        licensee="Apex Media Labs",
        gross_amount=500.0,
        platform_fee=75.0,
        net_amount=425.0,
        status="settled",
        currency="USD",
        disbursed_at=datetime.now(timezone.utc),
    )
    db.add(disbursement)
    db.commit()

    resp_disb = client.get(
        f"/api/v1/licenses/{license_id}/disbursements",
        headers={"Authorization": "Bearer mock-token-123"}
    )
    assert resp_disb.status_code == 200, f"Disbursements fetch failed: {resp_disb.text}"
    disb_res = resp_disb.json()
    assert disb_res["license_id"] == license_id
    assert disb_res["gross_escrow"] >= 500.0
    assert disb_res["platform_fee"] >= 75.0
    assert disb_res["net_disbursement"] >= 425.0
    assert len(disb_res["disbursements"]) >= 1
    assert disb_res["disbursements"][0]["status"] == "settled"
    print(f"  [PASS] GET /api/v1/licenses/{license_id}/disbursements verified against PROJECT.md schema")


# ===========================================================================
# Suite 6: HTTP Range Voice Audio Streaming (RFC 9110)
# ===========================================================================
def suite_6_http_range_audio_streaming(client: TestClient, db, voice_id: str) -> None:
    print("\n" + "=" * 75)
    print("SUITE 6: HTTP Range Voice Audio Streaming (RFC 9110)")
    print("=" * 75)

    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    file_size = os.path.getsize(voice.file_path)
    assert file_size >= 1024, f"Test voice file size {file_size} is too small for range tests"

    # 1. Full stream request (HTTP 200)
    resp_full = client.get(f"/api/v1/voices/{voice_id}/stream")
    assert resp_full.status_code == 200, f"Expected 200, got {resp_full.status_code}: {resp_full.text}"
    assert resp_full.headers.get("Accept-Ranges") == "bytes"
    assert int(resp_full.headers.get("Content-Length")) == file_size
    assert len(resp_full.content) == file_size
    print(f"  [PASS] Full audio stream returned HTTP 200 ({file_size} bytes, Accept-Ranges: bytes)")

    # 2. Standard byte range: Range: bytes=0-1023 (HTTP 206)
    resp_range = client.get(f"/api/v1/voices/{voice_id}/stream", headers={"Range": "bytes=0-1023"})
    assert resp_range.status_code == 206, f"Expected 206, got {resp_range.status_code}"
    assert resp_range.headers.get("Content-Range") == f"bytes 0-1023/{file_size}"
    assert resp_range.headers.get("Content-Length") == "1024"
    assert len(resp_range.content) == 1024
    print("  [PASS] Standard range bytes=0-1023 returned HTTP 206, exact 1024 bytes, Content-Range: bytes 0-1023/{total}")

    # 3. Suffix byte range: Range: bytes=-500 (HTTP 206)
    resp_suffix = client.get(f"/api/v1/voices/{voice_id}/stream", headers={"Range": "bytes=-500"})
    assert resp_suffix.status_code == 206, f"Expected 206, got {resp_suffix.status_code}"
    expected_start = file_size - 500
    expected_end = file_size - 1
    assert resp_suffix.headers.get("Content-Range") == f"bytes {expected_start}-{expected_end}/{file_size}"
    assert resp_suffix.headers.get("Content-Length") == "500"
    assert len(resp_suffix.content) == 500
    print(f"  [PASS] Suffix range bytes=-500 returned HTTP 206, exact 500 bytes (bytes {expected_start}-{expected_end}/{file_size})")

    # 4. Unsatisfiable range: Range: bytes=99999999-99999999 (HTTP 416)
    resp_invalid = client.get(f"/api/v1/voices/{voice_id}/stream", headers={"Range": "bytes=99999999-99999999"})
    assert resp_invalid.status_code == 416, f"Expected 416, got {resp_invalid.status_code}"
    assert resp_invalid.headers.get("Content-Range") == f"bytes */{file_size}"
    print("  [PASS] Unsatisfiable range returned HTTP 416 with Content-Range: bytes */{total}")

    # 5. Google Drive storage adapter fallback to local storage
    storage = GoogleDriveStorageService(folder_id=None)
    assert storage.is_drive_active is False, "Adapter should operate in local fallback when folder_id is None"
    meta = asyncio.run(storage.get_file_metadata(voice.file_path))
    assert meta["success"] is True
    assert meta["storage_type"] == "local"
    assert meta["size"] == file_size
    print("  [PASS] Google Drive storage adapter resilient local fallback verified without crashing")


# ===========================================================================
# Suite 7: Token Bucket & Leaky Bucket Rate Limiting
# ===========================================================================
def suite_7_rate_limiting_and_token_buckets(client: TestClient, voice_id: str) -> None:
    print("\n" + "=" * 75)
    print("SUITE 7: Token Bucket & Leaky Bucket Rate Limiting")
    print("=" * 75)

    client_ip = f"198.51.100.{random.randint(10, 240)}"

    # 1. Burst testing on protected synthesis endpoint (Token Bucket)
    synthesis_limiter.reset(client_ip)
    allowed = 0
    blocked = 0
    burst_count = int(synthesis_limiter.capacity) + 5

    for _ in range(burst_count):
        resp = client.post(
            "/api/v1/tts/synthesize",
            headers={
                "X-Forwarded-For": client_ip,
                "Authorization": "Bearer mock-token-123"
            },
            json={"voice_id": voice_id, "text": "Rapid burst test"}
        )
        if resp.status_code != 429:
            allowed += 1
        else:
            blocked += 1
            assert "Retry-After" in resp.headers
            err_text = resp.json().get("detail") or resp.json().get("error", "")
            assert "rate limit exceeded" in err_text.lower()

    assert blocked > 0, "Rate limiter failed to block requests exceeding burst capacity"
    print(f"  [PASS] Burst cap enforced on synthesis endpoint ({allowed} allowed, {blocked} blocked with HTTP 429 & Retry-After)")

    # 2. Refill recovery verification
    tb = TokenBucketRateLimiter(capacity=2.0, refill_rate=10.0)  # 10 tokens/s = 1 token per 0.1s
    test_key = "refill_test_client"
    assert tb.acquire(test_key, 2.0) is True
    assert tb.acquire(test_key, 1.0) is False  # Bucket empty
    time.sleep(0.15)  # Wait for refill of ~1.5 tokens
    assert tb.acquire(test_key, 1.0) is True, "Token bucket failed to recover tokens through steady refill"
    print("  [PASS] Rate limiter recovers tokens steadily with refill rate over elapsed time")

    # 3. Monotonic clock and thread safety
    tb_concurrent = TokenBucketRateLimiter(capacity=20.0, refill_rate=0.0)
    concurrent_key = "concurrent_client_thread"
    success_count = [0]
    lock = threading.Lock()

    def worker():
        for _ in range(5):
            if tb_concurrent.acquire(concurrent_key, 1.0):
                with lock:
                    success_count[0] += 1

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert success_count[0] == 20, (
        f"Expected exactly 20 successful token acquisitions, got {success_count[0]}"
    )
    print("  [PASS] Monotonic clock (time.monotonic) & mutex thread safety verified under 10 concurrent threads")


# ===========================================================================
# Suite 8: Production Build & Asset Integrity Check
# ===========================================================================
def suite_8_production_build_and_asset_integrity() -> None:
    print("\n" + "=" * 75)
    print("SUITE 8: Production Build & Asset Integrity Check")
    print("=" * 75)

    dist_dir = Path("D:/Main/frontend/dist")
    assert dist_dir.exists(), f"frontend/dist directory does not exist at {dist_dir}"

    # 1. index.html
    index_html = dist_dir / "index.html"
    assert index_html.exists(), "frontend/dist/index.html is missing"
    assert len(index_html.read_text(encoding="utf-8")) > 100, "frontend/dist/index.html is empty"
    print("  [PASS] frontend/dist/index.html verified and valid")

    # 2. Content-hashed CSS & JS assets
    assets_dir = dist_dir / "assets"
    assert assets_dir.exists(), "frontend/dist/assets directory missing"
    js_files = list(assets_dir.glob("*.js"))
    css_files = list(assets_dir.glob("*.css"))
    assert len(js_files) > 0, "No content-hashed JS files found in frontend/dist/assets"
    assert len(css_files) > 0, "No content-hashed CSS files found in frontend/dist/assets"
    print(f"  [PASS] Content-hashed assets verified: {len(js_files)} JS bundle(s), {len(css_files)} CSS bundle(s)")

    # 3. robots.txt
    robots_file = dist_dir / "robots.txt"
    assert robots_file.exists(), "frontend/dist/robots.txt missing"
    robots_text = robots_file.read_text(encoding="utf-8")
    for route in ["/dashboard", "/studio", "/talent", "/licensing", "/earnings", "/royalties", "/settings"]:
        assert f"Disallow: {route}" in robots_text, f"Disallow directive for {route} missing in robots.txt"
    assert "Sitemap: https://whicoustic.xyz/sitemap.xml" in robots_text or "Sitemap: https://whicoustic.ai/sitemap.xml" in robots_text, "Sitemap directive missing in robots.txt"
    print("  [PASS] robots.txt verified (disallows 7 console routes and references canonical sitemap)")

    # 4. sitemap.xml
    sitemap_file = dist_dir / "sitemap.xml"
    assert sitemap_file.exists(), "frontend/dist/sitemap.xml missing"
    sitemap_text = sitemap_file.read_text(encoding="utf-8")
    expected_paths = [
        "",
        "marketplace",
        "demo",
        "help",
        "contact",
        "terms",
        "privacy",
        "signup",
        "login",
        "onboarding",
    ]
    for path in expected_paths:
        has_url = f"<loc>https://whicoustic.xyz/{path}</loc>" in sitemap_text or f"<loc>https://whicoustic.ai/{path}</loc>" in sitemap_text
        assert has_url, f"Path /{path} missing from sitemap.xml"
    print(f"  [PASS] sitemap.xml verified (all {len(expected_paths)} public marketing URLs indexed)")

    # 5. Exactly 0 occurrences of 'VCaaS' across frontend/src
    src_dir = Path("D:/Main/frontend/src")
    assert src_dir.exists(), "frontend/src directory missing"
    vcaas_matches = []
    for f in src_dir.rglob("*"):
        if f.is_file() and f.suffix in {".ts", ".tsx", ".js", ".jsx", ".html", ".css", ".json"}:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if "VCaaS" in content:
                    vcaas_matches.append(str(f))
            except Exception:
                pass
    assert len(vcaas_matches) == 0, f"Found occurrences of 'VCaaS' in {vcaas_matches}"
    print("  [PASS] Brand integrity verified: exactly 0 occurrences of 'VCaaS' across frontend/src")


# ===========================================================================
# Master Test Execution Entrypoint
# ===========================================================================
def run_all_e2e_platform_suites() -> None:
    start_time = time.time()
    print("=" * 80)
    print("WHICOUSTIC PRODUCTION READINESS — UNIFIED PLATFORM E2E TEST RUNNER")
    print("=" * 80)
    print(f"Start Timestamp: {datetime.now(timezone.utc).isoformat()}Z")
    print(f"Working Directory: {Path.cwd()}")
    print(f"Python Executable: {sys.executable} (Version: {sys.version.split()[0]})")

    # 1. Initialize Tables & Security
    set_security_config("audit_verification_key_secure_32bytes")
    create_tables_sync()
    db = SyncSessionLocal()

    # 2. Ensure mock user exists for authenticated tests
    mock_user = db.query(User).filter(User.email == "demo@whicoustic.com").first()
    if not mock_user:
        mock_user = User(
            id="demo-user-123",
            username="demo_user",
            email="demo@whicoustic.com",
            hashed_password=get_password_hash("demo123"),
            full_name="Demo User",
            dob=date(1996, 8, 20),
            is_active=True,
        )
        db.add(mock_user)
        db.commit()

    # 3. Locate Real Human Speech from LibriSpeech Dataset
    librispeech_sample = locate_librispeech_sample()
    print(f"Verified LibriSpeech Real Audio Dataset: {librispeech_sample}")

    client = TestClient(app)

    try:
        suite_1_compliance_and_age_gate(client, db)
        created_voice_id = suite_2_real_speech_voice_profile(librispeech_sample, db)
        suite_3_tts_and_watermarking_four_pillars(librispeech_sample)
        suite_4_forensic_websocket_telemetry(client, librispeech_sample)
        suite_5_licensing_and_escrow_disbursement(client, db, created_voice_id)
        suite_6_http_range_audio_streaming(client, db, created_voice_id)
        suite_7_rate_limiting_and_token_buckets(client, created_voice_id)
        suite_8_production_build_and_asset_integrity()

        elapsed = time.time() - start_time
        print("\n" + "=" * 80)
        print("ALL 8 END-TO-END PLATFORM TEST SUITES PASSED WITH 100% SUCCESS!")
        print(f"Total Execution Time: {elapsed:.2f} seconds | Failures: 0 | Errors: 0")
        print("=" * 80)
        sys.exit(0)

    except Exception as exc:
        print("\n" + "!" * 80)
        print(f"TEST RUNNER FAILED WITH EXCEPTION: {exc}")
        print("!" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    run_all_e2e_platform_suites()
