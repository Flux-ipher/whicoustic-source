#!/usr/bin/env python3
"""
Load a fine-tuned XTTS v2 model from a local directory and synthesize audio.
Falls back to ZeroShotXTTS if loading fails.
"""
from __future__ import annotations

import io
from typing import Optional

import numpy as np
import soundfile as sf

try:
    import torch  # type: ignore
    from TTS.api import TTS  # type: ignore
    if hasattr(torch.serialization, "add_safe_globals"):
        from TTS.tts.configs.xtts_config import XttsConfig
        torch.serialization.add_safe_globals([XttsConfig])
except Exception:  # pragma: no cover
    TTS = None  # type: ignore
    torch = None  # type: ignore

from .xtts_zero_shot import ZeroShotXTTS


class FinetunedXTTS:
    async def __init__(self, model_dir: str) -> None:
        if TTS is None:
            # raise RuntimeError("Coqui TTS not available. Install 'TTS'.")
            print("WARNING: Coqui TTS not available. Running in MOCK mode.")
            self._tts = None
            return 
            
        self.device = "cuda" if (torch is not None and torch.cuda.is_available()) else "cpu"
        # Coqui TTS can load from local directory containing model files
        try:
            self._tts: Optional[TTS] = TTS(model_dir).to(self.device)  # type: ignore
        except Exception:
            self._tts = None

    def synthesize(
        self,
        text: str,
        speaker_wav_path: Optional[str] = None,
        language: str = "en",
        sample_rate: int = 22050,
    ) -> bytes:
        if self._tts is None:
            # Fallback
            return ZeroShotXTTS.instance().synthesize(text, speaker_wav_path or "", language)
        # If model expects a reference, pass it; otherwise Coqui will ignore
        audio: np.ndarray = self._tts.tts(text=text, speaker_wav=speaker_wav_path, language=language)
        buf = io.BytesIO()
        sf.write(buf, audio, samplerate=sample_rate, format="WAV")
        return buf.getvalue()
