"""
Milestone 4 Automated Test Suite: 6-Layer Forensic Verification WebSocket Telemetry.
Conforms strictly to:
- PROJECT.md § Frontend ↔ Backend Forensic WebSocket Stream
- Explicit "pass" | "anomaly" | "fail" status tags per layer
- 6 layers: anti_spoof, speaker_consistency, prosody, paralinguistic, semantic, watermark
- Top-level contract keys: timestamp, combined_risk_score, overall_authenticity_score, verdict
- Backward compatibility for DemoPage.tsx (layer1_antispoof .. layer6_watermark)
- Real human voice evaluation using D:\\New folder\\LibriSpeech
"""

import os
import sys
import time
import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.services.risk_scoring import assign_layer_status, combine_layer_results
from app.services.stream_session import StreamSession
from app.core.config import settings

LIBRISPEECH_SAMPLE = r"D:\New folder\LibriSpeech\dev-clean\1272\128104\1272-128104-0002.flac"


def test_layer_status_tag_assignment():
    """Verify explicit pass | anomaly | fail tag generation across all 6 defense layers."""
    print("Testing 6-layer status tag assignment logic...")

    # Layer 1: anti_spoof (higher authenticity score = more authentic)
    assert assign_layer_status("anti_spoof", {"score": 0.85}) == "pass"
    assert assign_layer_status("anti_spoof", {"score": 0.50}) == "anomaly"
    assert assign_layer_status("anti_spoof", {"score": 0.20}) == "fail"

    # Layer 2: speaker_consistency (cosine similarity)
    assert assign_layer_status("speaker_consistency", {"cosine_similarity": 0.90}) == "pass"
    assert assign_layer_status("speaker_consistency", {"cosine_similarity": 0.60}) == "anomaly"
    assert assign_layer_status("speaker_consistency", {"cosine_similarity": 0.30}) == "fail"

    # Layer 3: prosody
    assert assign_layer_status("prosody", {"score": 0.75}) == "pass"
    assert assign_layer_status("prosody", {"score": 0.50}) == "anomaly"
    assert assign_layer_status("prosody", {"score": 0.25}) == "fail"

    # Layer 4: paralinguistic
    assert assign_layer_status("paralinguistic", {"score": 0.70}) == "pass"
    assert assign_layer_status("paralinguistic", {"score": 0.45}) == "anomaly"
    assert assign_layer_status("paralinguistic", {"score": 0.15}) == "fail"

    # Layer 5: semantic
    assert assign_layer_status("semantic", {"score": 0.80}) == "pass"
    assert assign_layer_status("semantic", {"score": 0.50}) == "anomaly"
    assert assign_layer_status("semantic", {"score": 0.20}) == "fail"

    # Layer 6: watermark
    assert assign_layer_status("watermark", {"tampering_detected": False, "signature_valid": True}) == "pass"
    assert assign_layer_status("watermark", {"tampering_detected": True, "signature_valid": False}) == "fail"
    assert assign_layer_status("watermark", {"tampering_detected": False, "signature_valid": False}) == "fail"


def test_combined_layer_telemetry_contract():
    """Verify combined result JSON matching PROJECT.md § Frontend ↔ Backend Forensic WebSocket Stream."""
    print("Testing combined telemetry output structure...")
    
    mock_layers = {
        "anti_spoof": {"score": 0.88, "spoof_score": 0.12},
        "speaker_consistency": {"cosine_similarity": 0.92, "score": 0.92},
        "prosody": {"score": 0.85, "f0_mean_hz": 142.5},
        "paralinguistic": {"score": 0.78},
        "semantic": {"score": 0.82},
        "watermark": {"found": False, "detected": False, "tampering_detected": False}
    }
    
    weights = {
        "l1": {"score": 0.88, "weight": 0.35},
        "l2": {"score": 0.92, "weight": 0.15},
        "l3": {"score": 0.85, "weight": 0.15},
        "l4": {"score": 0.78, "weight": 0.10},
        "l5": {"score": 0.82, "weight": 0.25}
    }
    
    combined = combine_layer_results(mock_layers, weights)
    
    # Check top-level contract keys
    assert "timestamp" in combined, "Missing top-level timestamp"
    assert "combined_risk_score" in combined, "Missing top-level combined_risk_score"
    assert "overall_authenticity_score" in combined, "Missing top-level overall_authenticity_score"
    assert "verdict" in combined, "Missing top-level verdict"
    assert combined["verdict"] in {"AUTHENTIC", "SUSPICIOUS", "SYNTHETIC"}
    assert 0.0 <= combined["combined_risk_score"] <= 1.0
    assert 0.0 <= combined["overall_authenticity_score"] <= 1.0

    # Check 6 defense layers in layers dict
    layers = combined["layers"]
    for req_layer in ["anti_spoof", "speaker_consistency", "prosody", "paralinguistic", "semantic", "watermark"]:
        assert req_layer in layers, f"Missing required layer {req_layer}"
        layer_dict = layers[req_layer]
        assert "status" in layer_dict, f"Missing status in layer {req_layer}"
        assert layer_dict["status"] in {"pass", "anomaly", "fail"}

    # Check backward compatibility aliases for DemoPage.tsx
    assert "layer1_antispoof" in layers
    assert "layer2_speaker_consistency" in layers
    assert "layer3_prosody" in layers
    assert "layer4_paralinguistic" in layers
    assert "layer5_semantic" in layers
    assert "layer6_watermark" in layers


def test_websocket_stream_with_librispeech():
    """Verify WebSocket /api/v1/verify/stream with real human speech frames."""
    print("Testing WebSocket stream endpoint with real LibriSpeech audio frames...")
    
    # Enable test mock auth
    settings.MOCK_AUTH_ENABLED = True
    settings.ENVIRONMENT = "test"
    
    # Load real audio from LibriSpeech
    audio, sr = sf.read(LIBRISPEECH_SAMPLE)
    assert sr == 16000, f"Expected 16kHz LibriSpeech audio, got {sr}"
    
    # Convert to 16-bit signed PCM bytes
    pcm_16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    
    # 30ms frame = 480 samples = 960 bytes
    frame_samples = 480
    frame_bytes_len = frame_samples * 2
    
    client = TestClient(app)
    last_telemetry = None
    telemetry_frames_received = 0
    
    with client.websocket_connect("/api/v1/verify/stream?token=mock-token-123&mode=normal&sample_rate=16000") as ws:
        # Batch 1: Send 50 frames (1.50 seconds of real speech, surpassing MIN_ANALYSIS_SECONDS = 1.0s)
        for i in range(50):
            frame_data = pcm_16[i * frame_samples : (i + 1) * frame_samples].tobytes()
            ws.send_bytes(frame_data)
        
        # Receive the first analysis window verdict
        data1 = ws.receive_json()
        assert "layers" in data1
        telemetry_frames_received += 1
        last_telemetry = data1
        
        # Batch 2: Send another 25 frames (0.75 seconds, surpassing CADENCE_SECONDS = 0.5s)
        for i in range(50, 75):
            frame_data = pcm_16[i * frame_samples : (i + 1) * frame_samples].tobytes()
            ws.send_bytes(frame_data)
            
        data2 = ws.receive_json()
        assert "layers" in data2
        telemetry_frames_received += 1
        last_telemetry = data2

    print(f"Total forensic telemetry frames received during stream: {telemetry_frames_received}")
    assert telemetry_frames_received >= 2, "Expected at least 2 telemetry frames across stream"

    # Verify last telemetry frame conforms strictly to specification
    assert "timestamp" in last_telemetry
    assert "combined_risk_score" in last_telemetry
    assert "overall_authenticity_score" in last_telemetry
    assert "verdict" in last_telemetry
    assert last_telemetry["verdict"] in {"AUTHENTIC", "SUSPICIOUS", "SYNTHETIC"}

    layers = last_telemetry["layers"]
    for l_key in ["anti_spoof", "speaker_consistency", "prosody", "paralinguistic", "semantic", "watermark"]:
        assert l_key in layers, f"Layer {l_key} missing from live stream telemetry"
        assert layers[l_key]["status"] in {"pass", "anomaly", "fail"}

    # Human speech should have AUTHENTIC or SUSPICIOUS verdict (not synthetic)
    assert last_telemetry["verdict"] in {"AUTHENTIC", "SUSPICIOUS"}


def run_all_verify_stream_tests():
    print("=" * 70)
    print("RUNNING 6-LAYER FORENSIC WEBSOCKET TELEMETRY TEST SUITE (MILESTONE 4)")
    print("=" * 70)

    test_layer_status_tag_assignment()
    print("PASS: [1/3] 6-layer explicit pass/anomaly/fail status tag assignment")

    test_combined_layer_telemetry_contract()
    print("PASS: [2/3] Telemetry JSON output schema contract and backward compatibility")

    test_websocket_stream_with_librispeech()
    print("PASS: [3/3] Live WebSocket stream processing real LibriSpeech audio frames")

    print("=" * 70)
    print("ALL 3 FORENSIC TELEMETRY VERIFICATION SUITES PASSED (100% SUCCESS)!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_verify_stream_tests()
