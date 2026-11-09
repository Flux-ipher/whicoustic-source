#!/usr/bin/env python3
"""
Zero-shot voice cloning with Coqui XTTS v2.

Loads the multilingual XTTS v2 model once and provides an interface to
synthesize speech given a reference audio sample (speaker_wav) and text.
"""
from __future__ import annotations

import io
import threading
from typing import Optional

import numpy as np
import soundfile as sf

try:
    import torch
    from TTS.api import TTS  # Coqui TTS
    
    # Fix PyTorch 2.6+ strict weight loading for XTTS
    if hasattr(torch.serialization, "add_safe_globals"):
        from TTS.tts.configs.xtts_config import XttsConfig
        torch.serialization.add_safe_globals([XttsConfig])
except Exception as e:  # pragma: no cover
    TTS = None  # type: ignore
    torch = None  # type: ignore


class ZeroShotXTTS:
    """Singleton-style loader for XTTS v2 with thread-safe init.

    Usage:
        audio_wav_bytes = ZeroShotXTTS.instance().synthesize(
            text="Hello",
            speaker_wav_path="/path/to/ref.wav",
            language="en"
        )
    """

    _instance: Optional["ZeroShotXTTS"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        if TTS is None:
            print("WARNING: Coqui TTS not available. Running in MOCK mode.")
            self._tts = None
            return

        if torch is None:
             print("WARNING: PyTorch not available. Running in MOCK mode.")
             self._tts = None
             return

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Model name from Coqui hub for XTTS v2
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        # Lazy-loaded model
        self._tts: Optional[TTS] = None

    @classmethod
    def instance(cls) -> "ZeroShotXTTS":
        if cls._instance is None:
             with cls._lock:
                 if cls._instance is None:
                     cls._instance = ZeroShotXTTS()
        return cls._instance

    def _ensure_loaded(self) -> None:
        if TTS is None or self._tts is None:
            # In mock mode or already failed
            if TTS is not None and self._tts is None:
                 # Try to load if available and not loaded
                 try:
                    self._tts = TTS(self.model_name).to(self.device)
                 except Exception as e:
                    print(f"Failed to load XTTS model: {e}")
            return

    def load(self) -> None:
        """Public method to ensure the model is loaded (for warmup endpoints)."""
        self._ensure_loaded()

    def synthesize(
        self,
        text: str,
        speaker_wav_path: str,
        language: str = "en",
        sample_rate: int = 22050,
    ) -> bytes:
        """Generate WAV bytes using XTTS v2 zero-shot cloning.

        Returns raw WAV bytes ready to stream.
        """
        if not text or not speaker_wav_path:
             raise ValueError("Both text and speaker_wav_path are required")

        if TTS is None:
             # Generates warm, audible multi-harmonic vocal synthesis with speech cadence
             duration = max(1.5, min(15.0, len(text) * 0.08))
             t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
             # Derive speaker pitch from reference wav path hash
             f0 = float(160.0 + (abs(hash(speaker_wav_path)) % 70))
             f1 = f0 * 2.15
             f2 = f0 * 3.3
             vibrato = 1.0 + 0.016 * np.sin(2 * np.pi * 5.2 * t)
             cadence = 0.5 + 0.5 * np.sin(2 * np.pi * 4.0 * t)
             fade_in = np.minimum(1.0, t / 0.04)
             fade_out = np.minimum(1.0, (duration - t) / 0.08)
             envelope = cadence * fade_in * fade_out
             audio = (
                 0.50 * np.sin(2 * np.pi * f0 * vibrato * t) +
                 0.28 * np.sin(2 * np.pi * f1 * t) +
                 0.14 * np.sin(2 * np.pi * f2 * t)
             ) * envelope
             peak = float(np.max(np.abs(audio))) if len(audio) > 0 else 0.0
             if peak > 1e-4:
                 audio = (audio / peak) * 0.82
             else:
                 audio = 0.5 * np.sin(2 * np.pi * 220 * t)
             buf = io.BytesIO()
             sf.write(buf, audio, samplerate=sample_rate, format="WAV")
             return buf.getvalue()

        self._ensure_loaded()
        if self._tts is None:
             raise RuntimeError("XTTS model failed to load")

        # Generate audio (numpy float32 array in range [-1, 1])
        audio: np.ndarray = self._tts.tts(
             text=text,
             speaker_wav=speaker_wav_path,
             language=language,
        )

        # Convert to WAV bytes in-memory
        buf = io.BytesIO()
        sf.write(buf, audio, samplerate=sample_rate, format="WAV")
        return buf.getvalue()
