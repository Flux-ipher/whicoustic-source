"""
Voice Activity Detection Service — Phase 1 of Real-Time Streaming Detection.

Uses webrtcvad (Google's WebRTC VAD) to gate whether a given PCM chunk contains
speech. This is the fast, cheap gate that prevents silence frames from being
sent to the heavier analysis layers (librosa, faster-whisper, etc.).

webrtcvad constraints:
  - Sample rate must be one of: 8000, 16000, 32000, 48000 Hz
  - Frame duration must be one of: 10, 20, 30 ms
  - Audio must be raw 16-bit signed PCM (little-endian), mono

Aggressiveness modes (0–3):
  0 = least aggressive (more false positives — speech flagged in silence)
  3 = most aggressive (fewer false positives, may miss soft speech)
  2 is the recommended default for streaming audio.
"""
from __future__ import annotations

import struct
import numpy as np
from typing import Optional

try:
    import webrtcvad  # type: ignore
    _HAS_WEBRTCVAD = True
except ImportError:
    _HAS_WEBRTCVAD = False
    webrtcvad = None  # type: ignore


class VADService:
    """
    Voice Activity Detector wrapping webrtcvad.

    Usage:
        vad = VADService(aggressiveness=2)
        is_speech = vad.is_speech_bytes(chunk_bytes)  # raw PCM bytes
        # or from numpy:
        is_speech = vad.is_speech_array(audio_int16_chunk)
    """

    SUPPORTED_RATES = {8000, 16000, 32000, 48000}
    SUPPORTED_FRAME_MS = {10, 20, 30}

    def __init__(
        self,
        aggressiveness: int = 2,
        sample_rate: int = 16000,
        frame_ms: int = 30,
    ) -> None:
        if sample_rate not in self.SUPPORTED_RATES:
            raise ValueError(
                f"VADService: sample_rate must be one of {self.SUPPORTED_RATES}, got {sample_rate}"
            )
        if frame_ms not in self.SUPPORTED_FRAME_MS:
            raise ValueError(
                f"VADService: frame_ms must be one of {self.SUPPORTED_FRAME_MS}, got {frame_ms}"
            )

        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        # Number of int16 samples per frame
        self.frame_samples = int(sample_rate * frame_ms / 1000)
        # Expected bytes per frame (2 bytes per int16 sample)
        self.frame_bytes = self.frame_samples * 2

        if _HAS_WEBRTCVAD:
            self._vad = webrtcvad.Vad(aggressiveness)
        else:
            self._vad = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_speech_bytes(self, frame: bytes) -> bool:
        """
        Check whether a raw PCM frame contains speech.

        Args:
            frame: Raw bytes of exactly `frame_bytes` length.
                   Must be 16-bit signed PCM, mono, at `sample_rate`.

        Returns:
            True if speech detected, False otherwise.
            If webrtcvad is not installed, always returns True (pass-through).
        """
        if self._vad is None:
            # No webrtcvad — pass everything through so streaming still works
            return True

        if len(frame) != self.frame_bytes:
            # Wrong frame size — skip silently rather than crash
            return False

        try:
            return self._vad.is_speech(frame, self.sample_rate)
        except Exception:
            return True  # conservative — pass through on errors

    def is_speech_array(self, audio: np.ndarray) -> bool:
        """
        Check whether a numpy int16 array chunk contains speech.

        If the chunk is not exactly `frame_samples` long, the first
        `frame_samples` samples are used (or it's zero-padded if shorter).

        Args:
            audio: 1-D numpy array, dtype int16, mono.

        Returns:
            True if speech detected, False otherwise.
        """
        # Ensure int16
        if audio.dtype != np.int16:
            audio = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)

        # Pad or truncate to exactly one frame
        if len(audio) < self.frame_samples:
            audio = np.pad(audio, (0, self.frame_samples - len(audio)))
        else:
            audio = audio[: self.frame_samples]

        frame_bytes = audio.tobytes()
        return self.is_speech_bytes(frame_bytes)

    def segment_speech(self, audio: np.ndarray) -> list[tuple[int, int]]:
        """
        Scan a full audio array and return (start, end) sample indices of
        speech segments. Useful for gating longer buffers before running
        heavier layer analysis.

        Args:
            audio: 1-D numpy int16 array.

        Returns:
            List of (start_sample, end_sample) tuples.
        """
        if audio.dtype != np.int16:
            audio = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)

        segments: list[tuple[int, int]] = []
        in_speech = False
        seg_start = 0

        for i in range(0, len(audio) - self.frame_samples + 1, self.frame_samples):
            frame = audio[i : i + self.frame_samples]
            speech = self.is_speech_array(frame)

            if speech and not in_speech:
                in_speech = True
                seg_start = i
            elif not speech and in_speech:
                in_speech = False
                segments.append((seg_start, i))

        # Close any open segment at the end of the buffer
        if in_speech:
            segments.append((seg_start, len(audio)))

        return segments
