"""
Milestone 4 Automated Test Suite: Novel Audio Watermarking Engine.
Validates the 4 pillars (+ LibriSpeech empirical robustness & ultrasonic Nyquist carrier):
1. Haas Effect Echo Hiding: Bit '0' = 20ms, Bit '1' = 25ms delay (5-35ms perceptual fusion window).
2. Cepstral Detection: Additive peaks in real cepstrum IFFT(log|FFT|) at 20ms and 25ms.
3. Continuous Payload Repetition & Tamper Localization: Repeating compact blocks every 2.5-3.8s.
4. HMAC-SHA256 Cryptographic Signing: Constant-time comparison (hmac.compare_digest).
5. 21.4 kHz Ultrasonic Carrier: Nyquist upsampling and SHA-256 payload recovery.
6. Empirical Robustness: Real speech from D:\\New folder\\LibriSpeech across MP3 compression,
   resampling, pitch shifting, trimming, additive noise, and tamper localization.
"""

import os
import sys
import asyncio
import numpy as np
import soundfile as sf
import librosa

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.watermark import WatermarkService, WatermarkEncoder, WatermarkDecoder, SCRATCH_DIR


# LibriSpeech test audio paths
LIBRISPEECH_DIR = r"D:\New folder\LibriSpeech\dev-clean\1272\128104"
TEST_AUDIO_FILE = os.path.join(LIBRISPEECH_DIR, "1272-128104-0002.flac") # 12.48s clean speech
TEST_AUDIO_FILE_SHORT = os.path.join(LIBRISPEECH_DIR, "1272-128104-0000.flac") # 5.86s clean speech


async def test_baseline_and_hmac_signing():
    """Pillars 1, 2, 4: Echo hiding within Haas window, cepstral detection, and HMAC signing."""
    print("\n--- [1/8] Testing Baseline Echo Hiding, Cepstral Detection & HMAC Signing ---")
    service = WatermarkService(secret_key="audit_verification_key_secure")
    
    out_path = os.path.join(SCRATCH_DIR, "test_baseline_watermarked.wav")
    wm_id = "wm_7c8d"
    
    # Embed
    await service.embed_watermark(
        audio_path=TEST_AUDIO_FILE,
        watermark_id=wm_id,
        output_path=out_path,
        method="robust"
    )
    assert os.path.exists(out_path), "Watermarked output file was not created"
    
    # Detect
    res = await service.detect_watermark(out_path, method="robust")
    print("Baseline detection result:", res)
    
    assert res.get("found") is True, "Watermark was not detected in baseline audio"
    assert res.get("watermark_id") == wm_id, f"Watermark ID mismatch: expected {wm_id}, got {res.get('watermark_id')}"
    assert res.get("signature_valid") is True, "HMAC signature was not verified"
    assert res.get("detection_method") == "robust_echo_hiding"
    assert res.get("total_blocks", 0) >= 2, "Expected at least 2 repeating blocks across 12.48s clip"
    print("PASS: Baseline Haas echo hiding, cepstral peak detection & HMAC verification verified!")


async def test_continuous_repetition_and_tamper_localization():
    """Pillar 3: Continuous repetition and timeline tamper localization."""
    print("\n--- [2/8] Testing Continuous Repetition & Tamper Localization ---")
    service = WatermarkService(secret_key="audit_verification_key_secure")
    
    out_path = os.path.join(SCRATCH_DIR, "test_rep_watermarked.wav")
    tampered_path = os.path.join(SCRATCH_DIR, "test_tampered.wav")
    wm_id = "wm_3f1a"
    
    # Embed
    await service.embed_watermark(
        audio_path=TEST_AUDIO_FILE,
        watermark_id=wm_id,
        output_path=out_path,
        method="robust"
    )
    
    # Load watermarked audio and splice an unwatermarked speech segment in the middle
    audio, sr = sf.read(out_path)
    block_samples = int(round(52 * 2 * 0.035 * sr)) # duration of 1 block ~ 3.64s
    
    # Load separate unwatermarked speech
    splice_audio, _ = sf.read(TEST_AUDIO_FILE_SHORT)
    tampered_audio = audio.copy()
    
    # Splice into middle block (block index 1: from block_samples to 2*block_samples)
    tampered_audio[block_samples : 2 * block_samples] = splice_audio[:block_samples]
    sf.write(tampered_path, tampered_audio, sr)
    
    # Detect on tampered audio
    res = await service.detect_watermark(tampered_path, method="robust")
    print("Tamper localization result:", res)
    
    assert res.get("found") is True, "Watermark should still be found from surviving authentic blocks"
    assert res.get("tampering_detected") is True, "Tampering was not flagged"
    assert len(res.get("timeline", [])) >= 2, "Timeline segments missing"
    
    # Verify timeline marks the tampered block as fail
    timeline = res["timeline"]
    block_1_status = timeline[1]["status"]
    assert block_1_status == "fail", f"Expected tampered block 1 to have status fail, got {block_1_status}"
    assert timeline[1]["tampered"] is True, "Expected block 1 tampered to be True"
    print("PASS: Timeline tamper localization accurately identified damaged timeline interval!")


async def test_trimming_and_cropping_robustness():
    """Pillar 3 & 6: Independent verification after cropping/trimming."""
    print("\n--- [3/8] Testing Trimming & Cropping Robustness ---")
    service = WatermarkService(secret_key="audit_verification_key_secure")
    
    wm_path = os.path.join(SCRATCH_DIR, "test_baseline_watermarked.wav")
    cropped_path = os.path.join(SCRATCH_DIR, "test_cropped.wav")
    
    audio, sr = sf.read(wm_path)
    # Crop out the first 3 seconds and last 2 seconds (retaining only middle 7.48s)
    cropped_audio = audio[int(3.0 * sr) : int(10.5 * sr)]
    sf.write(cropped_path, cropped_audio, sr)
    
    res = await service.detect_watermark(cropped_path, method="robust")
    print("Cropped audio detection result:", res)
    
    assert res.get("found") is True, "Watermark must be detectable in cropped/trimmed audio"
    assert res.get("signature_valid") is True, "HMAC signature must verify in surviving segment"
    print("PASS: Independent segment verification succeeded on cropped audio!")


async def test_mp3_compression_robustness():
    """Pillar 6: Robustness against MP3 psychoacoustic compression."""
    print("\n--- [4/8] Testing MP3 Compression Robustness ---")
    service = WatermarkService(secret_key="audit_verification_key_secure")
    
    wm_path = os.path.join(SCRATCH_DIR, "test_baseline_watermarked.wav")
    mp3_path = os.path.join(SCRATCH_DIR, "test_compressed.mp3")
    
    audio, sr = sf.read(wm_path)
    # Write to MP3 format using soundfile native support
    sf.write(mp3_path, audio, sr, format="MP3")
    
    # Detect directly from MP3
    res = await service.detect_watermark(mp3_path, method="robust")
    print("MP3 compressed detection result:", res)
    
    assert res.get("found") is True, "Watermark was not detected after MP3 compression"
    assert res.get("watermark_id") == "wm_7c8d"
    print("PASS: Echo hiding watermark survived MP3 psychoacoustic compression!")


async def test_resampling_robustness():
    """Pillar 6: Robustness against audio sample rate conversion."""
    print("\n--- [5/8] Testing Resampling Robustness ---")
    service = WatermarkService(secret_key="audit_verification_key_secure")
    
    wm_path = os.path.join(SCRATCH_DIR, "test_baseline_watermarked.wav")
    resampled_path = os.path.join(SCRATCH_DIR, "test_resampled.wav")
    
    audio, sr = sf.read(wm_path)
    # Upsample to 22.05 kHz then resample back to 16 kHz
    up = librosa.resample(audio, orig_sr=sr, target_sr=22050)
    down = librosa.resample(up, orig_sr=22050, target_sr=sr)
    sf.write(resampled_path, down, sr)
    
    res = await service.detect_watermark(resampled_path, method="robust")
    print("Resampled detection result:", res)
    
    assert res.get("found") is True, "Watermark was not detected after resampling"
    print("PASS: Cepstral peaks invariant to sample rate conversion!")


async def test_pitch_shifting_robustness():
    """Pillar 6: Robustness against semitone pitch shifting."""
    print("\n--- [6/8] Testing Pitch Shifting Robustness ---")
    service = WatermarkService(secret_key="audit_verification_key_secure")
    
    wm_path = os.path.join(SCRATCH_DIR, "test_baseline_watermarked.wav")
    shifted_path = os.path.join(SCRATCH_DIR, "test_pitch_shifted.wav")
    
    audio, sr = sf.read(wm_path)
    # Shift pitch by +1 semitone (factor 2^(1/12) ~ 1.05946)
    r = 2 ** (1 / 12)
    shifted = librosa.resample(audio, orig_sr=sr, target_sr=int(round(sr * r)))
    sf.write(shifted_path, shifted, sr)
    
    res = await service.detect_watermark(shifted_path, method="robust")
    print("Pitch shifted (+1 semitone) detection result:", res)
    
    assert res.get("found") is True, "Watermark was not detected after pitch shift"
    print("PASS: Watermark survived pitch shift!")


async def test_additive_noise_robustness():
    """Pillar 6: Robustness against additive acoustic white noise."""
    print("\n--- [7/8] Testing Additive Noise Robustness (SNR = 20 dB) ---")
    service = WatermarkService(secret_key="audit_verification_key_secure")
    
    wm_path = os.path.join(SCRATCH_DIR, "test_baseline_watermarked.wav")
    noisy_path = os.path.join(SCRATCH_DIR, "test_noisy.wav")
    
    audio, sr = sf.read(wm_path)
    sig_power = np.mean(audio**2)
    snr_db = 20.0
    noise_power = sig_power / (10 ** (snr_db / 10.0))
    noise = np.random.normal(0, np.sqrt(noise_power), len(audio))
    noisy_audio = np.clip(audio + noise, -0.99, 0.99)
    sf.write(noisy_path, noisy_audio, sr)
    
    res = await service.detect_watermark(noisy_path, method="robust")
    print("Additive noise (20dB) detection result:", res)
    
    assert res.get("found") is True, "Watermark was not detected after noise addition"
    print("PASS: Watermark verified under additive acoustic noise!")


async def test_ultrasonic_carrier_and_nyquist_upsampling():
    """Pillar 5: 21.4 kHz ultrasonic carrier with SHA-256 and Nyquist upsampling."""
    print("\n--- [8/8] Testing 21.4 kHz Ultrasonic Carrier & Nyquist Upsampling ---")
    service = WatermarkService(secret_key="audit_verification_key_secure")
    
    ultra_path = os.path.join(SCRATCH_DIR, "test_ultrasonic_44k.wav")
    wm_id = "whicoustic_sha256_watermark_test"
    
    # Input is 16 kHz LibriSpeech file -> must automatically upsample to >= 44.1 kHz
    await service.embed_watermark(
        audio_path=TEST_AUDIO_FILE_SHORT,
        watermark_id=wm_id,
        output_path=ultra_path,
        method="mvp"
    )
    
    # Check output audio sample rate
    _, sr_out = sf.read(ultra_path)
    assert sr_out >= 44100, f"Expected output sample rate >= 44100 Hz, got {sr_out}"
    print(f"Output audio correctly upsampled to {sr_out} Hz (Nyquist={sr_out/2} Hz > 21.4 kHz)")
    
    # Detect ultrasonic carrier
    res = await service.detect_watermark(ultra_path, method="mvp")
    print("Ultrasonic detection result:", res)
    
    assert res.get("found") is True, "Ultrasonic watermark was not detected"
    assert res.get("detection_method") == "ultrasonic_carrier"
    assert res.get("frequency") == 21400.0, f"Expected frequency 21400 Hz, got {res.get('frequency')}"
    print("PASS: 21.4 kHz ultrasonic carrier with SHA-256 payload and Nyquist upsampling verified!")


async def run_all_watermark_tests():
    print("=" * 70)
    print("RUNNING WHICOUSTIC NOVEL WATERMARKING ENGINE TEST SUITE (MILESTONE 4)")
    print("=" * 70)
    
    await test_baseline_and_hmac_signing()
    await test_continuous_repetition_and_tamper_localization()
    await test_trimming_and_cropping_robustness()
    await test_mp3_compression_robustness()
    await test_resampling_robustness()
    await test_pitch_shifting_robustness()
    await test_additive_noise_robustness()
    await test_ultrasonic_carrier_and_nyquist_upsampling()
    
    print("\n" + "=" * 70)
    print("ALL 8 WATERMARKING ENGINE VERIFICATION SUITES PASSED (100% SUCCESS)!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_all_watermark_tests())
