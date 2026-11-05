import os
import sys
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
import tempfile
import asyncio
import pytest

# Add backend to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.watermark import WatermarkService

def generate_test_audio(duration=10, sr=44100):
    """Generate a synthetic harmonic signal for testing."""
    t = np.linspace(0, duration, duration * sr, False)
    audio = np.sin(2 * np.pi * 440 * t) * 0.3
    audio += np.sin(2 * np.pi * 880 * t) * 0.2
    audio += np.sin(2 * np.pi * 1760 * t) * 0.1
    # Add some noise
    audio += np.random.normal(0, 0.05, len(audio))
    return np.clip(audio, -0.99, 0.99), sr

import pytest_asyncio

@pytest.fixture
def watermark_service():
    return WatermarkService(secret_key="test_secret_key_for_robustness")

@pytest.fixture
def base_audio(tmp_path):
    audio, sr = generate_test_audio(duration=15)
    file_path = str(tmp_path / "base.wav")
    sf.write(file_path, audio, sr)
    return file_path, sr

@pytest_asyncio.fixture
async def watermarked_audio(watermark_service, base_audio, tmp_path):
    base_path, _ = base_audio
    wm_id = "test_wm_12345"
    out_path = await watermark_service.embed_watermark(
        audio_path=base_path,
        watermark_id=wm_id,
        method="robust"
    )
    return out_path, wm_id

@pytest.mark.asyncio
async def test_baseline_detection(watermark_service, watermarked_audio):
    wm_path, wm_id = await watermarked_audio
    result = await watermark_service.detect_watermark(wm_path, method="robust")
    assert result.get("found") is True
    assert result.get("watermark_id") == wm_id

@pytest.mark.asyncio
async def test_mp3_compression(watermark_service, watermarked_audio, tmp_path):
    wm_path, wm_id = await watermarked_audio
    bitrates = ["128k", "96k", "64k"]
    
    print("\n--- MP3 Compression Results ---")
    for br in bitrates:
        mp3_path = str(tmp_path / f"test_{br}.mp3")
        wav_path = str(tmp_path / f"test_{br}.wav")
        
        # Compress
        audio = AudioSegment.from_wav(wm_path)
        audio.export(mp3_path, format="mp3", bitrate=br)
        
        # Decompress
        audio = AudioSegment.from_mp3(mp3_path)
        audio.export(wav_path, format="wav")
        
        result = await watermark_service.detect_watermark(wav_path, method="robust")
        found = result.get("found", False)
        print(f"Bitrate {br}: {'PASS' if found else 'FAIL'}")
        if br == "128k":
            assert found

@pytest.mark.asyncio
async def test_resampling(watermark_service, watermarked_audio, tmp_path):
    wm_path, wm_id = await watermarked_audio
    rates = [44100, 22050, 16000]
    
    print("\n--- Resampling Results ---")
    audio, sr = librosa.load(wm_path, sr=None)
    
    for rate in rates:
        resampled = librosa.resample(audio, orig_sr=sr, target_sr=rate)
        out_path = str(tmp_path / f"resampled_{rate}.wav")
        sf.write(out_path, resampled, rate)
        
        result = await watermark_service.detect_watermark(out_path, method="robust")
        found = result.get("found", False)
        print(f"Sample Rate {rate}: {'PASS' if found else 'FAIL'}")
        if rate >= 16000:
            assert found

@pytest.mark.asyncio
async def test_pitch_shifting(watermark_service, watermarked_audio, tmp_path):
    wm_path, wm_id = await watermarked_audio
    shifts = [2, -2] # semitones
    
    print("\n--- Pitch Shifting Results ---")
    audio, sr = librosa.load(wm_path, sr=None)
    
    for shift in shifts:
        shifted = librosa.effects.pitch_shift(audio, sr=sr, n_steps=shift)
        out_path = str(tmp_path / f"shifted_{shift}.wav")
        sf.write(out_path, shifted, sr)
        
        result = await watermark_service.detect_watermark(out_path, method="robust")
        found = result.get("found", False)
        print(f"Pitch Shift {shift}: {'PASS' if found else 'FAIL'}")
        # Spread spectrum usually survives small pitch shifts
        assert found

@pytest.mark.asyncio
async def test_trimming(watermark_service, watermarked_audio, tmp_path):
    wm_path, wm_id = await watermarked_audio
    
    print("\n--- Trimming Results ---")
    audio, sr = librosa.load(wm_path, sr=None)
    
    # Trim 50% from start and 25% from end (leaving 25% to 75% of original)
    start_idx = int(0.50 * len(audio))
    end_idx = int(0.75 * len(audio))
    
    trimmed = audio[start_idx:end_idx]
    out_path = str(tmp_path / "trimmed.wav")
    sf.write(out_path, trimmed, sr)
    
    result = await watermark_service.detect_watermark(out_path, method="robust")
    found = result.get("found", False)
    print(f"Trimmed (middle 25%): {'PASS' if found else 'FAIL'}")
    assert found

@pytest.mark.asyncio
async def test_additive_noise(watermark_service, watermarked_audio, tmp_path):
    wm_path, wm_id = await watermarked_audio
    snr_db = [20, 10, 5]
    
    print("\n--- Additive Noise Results ---")
    audio, sr = librosa.load(wm_path, sr=None)
    signal_power = np.mean(audio ** 2)
    
    for snr in snr_db:
        noise_power = signal_power / (10 ** (snr / 10))
        noise = np.random.normal(0, np.sqrt(noise_power), len(audio))
        noisy_audio = audio + noise
        noisy_audio = np.clip(noisy_audio, -0.99, 0.99)
        
        out_path = str(tmp_path / f"noisy_{snr}.wav")
        sf.write(out_path, noisy_audio, sr)
        
        result = await watermark_service.detect_watermark(out_path, method="robust")
        found = result.get("found", False)
        print(f"SNR {snr}dB: {'PASS' if found else 'FAIL'}")
        if snr >= 10:
            assert found
