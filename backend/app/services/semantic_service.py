"""
Semantic / Linguistic-Acoustic Alignment Service — Layer 5 of the 6-layer defense pipeline.

Uses faster-whisper to transcribe the audio, then analyses:
  1. Speech rate (words per minute) — TTS is often unnaturally fast or robotically even.
  2. Inter-word pause consistency — human speech has natural variation in pause length;
     TTS tends to produce mechanically consistent pauses.
  3. Transcription confidence — very high Whisper confidence on incoherent or
     nonsensical audio may indicate the audio contains synthetic artifacts.

DEPENDENCIES:
  faster-whisper>=0.10.0   (add to requirements.txt)

INSTALLATION:
  pip install faster-whisper

MODEL:
  Uses the 'tiny' model by default for speed. For production, use 'small' or 'medium'
  for better accuracy. The model is downloaded once and cached in ~/.cache/huggingface/.

LAYER 4 NOTE:
  Paralinguistic coherence (tone/content mismatch) is NOT yet implemented — it
  requires a speech-emotion-recognition (SER) model to compare the emotional
  valence of the audio against the sentiment of the transcription. That requires
  an additional SER model (e.g. facebook/wav2vec2-large-xlsr-53-emotion) and is
  tracked as a future enhancement.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import numpy as np

# faster-whisper is an optional dependency; fail gracefully if not installed
try:
    from faster_whisper import WhisperModel  # type: ignore
    _HAS_WHISPER = True
except ImportError:
    WhisperModel = None  # type: ignore
    _HAS_WHISPER = False


class SemanticService:
    """Layer 5: Semantic / Linguistic-Acoustic Alignment analyser."""

    _MODEL_SIZE = "tiny"   # swap to 'small' or 'medium' for higher accuracy
    _DEVICE = "cpu"         # swap to 'cuda' when GPU is available
    _COMPUTE_TYPE = "int8"  # float16 on GPU, int8 on CPU

    def __init__(self) -> None:
        self._model: Optional[WhisperModel] = None

    def _ensure_model(self) -> None:
        if self._model is None and _HAS_WHISPER:
            self._model = WhisperModel(
                self._MODEL_SIZE,
                device=self._DEVICE,
                compute_type=self._COMPUTE_TYPE,
            )

    def analyse(self, audio_path: str) -> Dict[str, Any]:
        """Run semantic analysis on an audio file.

        Args:
            audio_path: Path to a WAV/FLAC/MP3 file.

        Returns:
            Dict with:
              - authenticity_score   (float, 0–1)
              - transcription        (str | None)
              - speech_rate_wpm      (float | None)
              - pause_consistency_score (float, 0–1, lower = more consistent/suspicious)
              - word_count           (int)
              - duration_s           (float | None)
              - anomaly_flags        (list[str])
              - engine               (str)
              - available            (bool)
        """
        if not _HAS_WHISPER:
            return {
                "authenticity_score": 0.5,   # neutral — can't evaluate
                "transcription": None,
                "speech_rate_wpm": None,
                "pause_consistency_score": None,
                "word_count": 0,
                "duration_s": None,
                "anomaly_flags": ["faster-whisper not installed — Layer 5 unavailable"],
                "engine": "semantic_whisper",
                "available": False,
            }

        try:
            self._ensure_model()
            return self._analyse_with_whisper(audio_path)
        except Exception as exc:
            return {
                "authenticity_score": 0.5,
                "transcription": None,
                "speech_rate_wpm": None,
                "pause_consistency_score": None,
                "word_count": 0,
                "duration_s": None,
                "anomaly_flags": [f"Transcription error: {exc}"],
                "engine": "semantic_whisper",
                "available": True,
            }

    def analyse_segment(self, audio: "np.ndarray", sr: int = 16000) -> Dict[str, Any]:
        """
        Run semantic analysis on a short VAD-gated audio segment (streaming Phase 6, Option A).

        Runs faster-whisper on a 2–4 second numpy array segment rather than a
        full file. Called from StreamSession as an asyncio.Task — does NOT block
        the fast-path verdict loop. Results are merged into the next verdict push.

        Accuracy is somewhat lower per-segment than full-file transcription (less
        context for Whisper) but is good enough for detecting the key anomaly
        signals (speech rate, pause structure, repetition).

        Args:
            audio: 1-D float32 numpy array, values in [-1, 1], mono, at `sr`.
            sr: Sample rate in Hz (default 16000).

        Returns:
            Same dict shape as analyse() so StreamSession can merge it uniformly.
        """
        import numpy as _np
        import tempfile
        import soundfile as sf  # type: ignore

        if not _HAS_WHISPER:
            return {
                "authenticity_score": 0.5,
                "transcription": None,
                "anomaly_flags": ["faster-whisper not installed"],
                "engine": "semantic_whisper",
                "available": False,
            }

        audio = _np.asarray(audio, dtype=_np.float32)
        if audio.ndim > 1:
            audio = _np.mean(audio, axis=-1)

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            sf.write(tmp_path, audio, sr)
            self._ensure_model()
            return self._analyse_with_whisper(tmp_path)
        except Exception as exc:
            return {
                "authenticity_score": 0.5,
                "transcription": None,
                "anomaly_flags": [f"Segment transcription error: {exc}"],
                "engine": "semantic_whisper",
                "available": True,
            }
        finally:
            if tmp_path:
                try:
                    import os as _os
                    _os.unlink(tmp_path)
                except Exception:
                    pass



    def analyse_array(self, audio: np.ndarray, sr: int = 16000) -> Dict[str, Any]:
        """Run semantic analysis on an in-memory 16kHz float32 audio array."""
        if not _HAS_WHISPER:
            return {
                "authenticity_score": 0.5,
                "transcription": None,
                "speech_rate_wpm": None,
                "pause_consistency_score": None,
                "word_count": 0,
                "duration_s": None,
                "anomaly_flags": ["faster-whisper not installed — Layer 5 unavailable"],
                "engine": "semantic_whisper",
                "available": False,
            }

        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=-1)

        try:
            self._ensure_model()
            return self._analyse_with_whisper(audio)
        except Exception as exc:
            return {
                "authenticity_score": 0.5,
                "transcription": None,
                "speech_rate_wpm": None,
                "pause_consistency_score": None,
                "word_count": 0,
                "duration_s": None,
                "anomaly_flags": [f"Array transcription error: {exc}"],
                "engine": "semantic_whisper",
                "available": True,
            }

    def _analyse_with_whisper(self, audio_input: Any) -> Dict[str, Any]:
        if isinstance(audio_input, np.ndarray):
            audio_data = np.asarray(audio_input, dtype=np.float32)
            duration_fallback = float(len(audio_data) / 16000)
        else:
            audio_data = audio_input
            duration_fallback = None

        segments_iter, info = self._model.transcribe(  # type: ignore[union-attr]
            audio_data,
            word_timestamps=True,
            vad_filter=True,
        )

        segments: List[Any] = list(segments_iter)

        # Build flat word list with timestamps
        words: List[Dict[str, Any]] = []
        for seg in segments:
            if seg.words:
                for w in seg.words:
                    words.append({
                        "word": w.word.strip(),
                        "start": w.start,
                        "end": w.end,
                        "probability": w.probability,
                    })

        transcription = " ".join(w["word"] for w in words)
        word_count = len(words)
        audio_duration = info.duration if hasattr(info, "duration") and info.duration else duration_fallback

        anomaly_flags: List[str] = []

        # ── Speech rate ────────────────────────────────────────────────────
        speech_rate_wpm: Optional[float] = None
        if audio_duration and audio_duration > 0 and word_count > 0:
            speech_rate_wpm = round(word_count / (audio_duration / 60.0), 1)
            # Natural range: ~100–185 WPM; TTS often outside this
            if speech_rate_wpm > 210:
                anomaly_flags.append(f"Unusually fast speech rate: {speech_rate_wpm} WPM")
            elif speech_rate_wpm < 55 and word_count > 5:
                anomaly_flags.append(f"Unusually slow speech rate: {speech_rate_wpm} WPM")

        # ── Pause consistency ──────────────────────────────────────────────
        pause_consistency_score: Optional[float] = None
        if len(words) >= 3:
            inter_word_gaps = []
            for i in range(1, len(words)):
                gap = words[i]["start"] - words[i - 1]["end"]
                if 0 <= gap < 2.0:   # ignore long pauses (sentence breaks)
                    inter_word_gaps.append(gap)

            if len(inter_word_gaps) >= 3:
                gaps_arr = np.array(inter_word_gaps)
                gap_cv = float(np.std(gaps_arr) / (np.mean(gaps_arr) + 1e-6))
                # Natural speech CV for inter-word gaps: 0.4–2.0
                # TTS tends to produce very low CV (< 0.25 = mechanically even)
                pause_consistency_score = round(float(np.clip(gap_cv / 0.45, 0.0, 1.0)), 4)
                if gap_cv < 0.22:
                    anomaly_flags.append(
                        f"Unnaturally consistent inter-word pauses (CV={gap_cv:.3f})"
                    )

        # ── Transcription confidence ───────────────────────────────────────
        if words:
            avg_prob = float(np.mean([w["probability"] for w in words]))
            if avg_prob > 0.98 and word_count > 10:
                anomaly_flags.append(
                    f"Suspiciously high transcription confidence (avg={avg_prob:.3f})"
                )

        # ── Authenticity score ─────────────────────────────────────────────
        sub_scores: List[float] = []

        # Speech rate score (110 - 185 WPM is natural human speech)
        if speech_rate_wpm is not None:
            if 110 <= speech_rate_wpm <= 185:
                rate_score = 1.0
            elif speech_rate_wpm > 185:
                rate_score = float(np.clip(1.0 - (speech_rate_wpm - 185) / 100.0, 0.1, 1.0))
            else:
                rate_score = float(np.clip(1.0 - (110 - speech_rate_wpm) / 70.0, 0.1, 1.0))
            sub_scores.append(rate_score)

        # Pause consistency score (higher = more natural variation = more authentic)
        if pause_consistency_score is not None:
            sub_scores.append(pause_consistency_score)

        authenticity_score = float(np.mean(sub_scores)) if sub_scores else 0.5

        return {
            "authenticity_score": round(authenticity_score, 4),
            "transcription": transcription or None,
            "speech_rate_wpm": speech_rate_wpm,
            "pause_consistency_score": pause_consistency_score,
            "word_count": word_count,
            "duration_s": round(audio_duration, 2) if audio_duration else None,
            "anomaly_flags": anomaly_flags,
            "engine": "semantic_whisper",
            "available": True,
        }
