"""
StreamSession — per-connection state for real-time streaming deepfake detection.

Each WebSocket connection gets its own StreamSession. It holds:
  - A circular buffer of raw int16 audio samples
  - Per-layer running state (pitch history for Layer 3 CV tracking)
  - VADService reference to gate analysis on speech frames
  - An async task slot for background Layer 6 watermark detection

Design principles from the implementation plan:
  - Layers 1–4 run on every speech-containing window (fast path)
  - Layer 5 (Whisper) runs on its own cadence on VAD-gated segments
  - Layer 6 (watermark) is launched as an asyncio.Task when buffer >= 7s
  - All scoring uses the shared risk_scoring.combine_layer_results()
"""
from __future__ import annotations

import asyncio
import logging
from collections import deque
from typing import Any, Dict, Optional

import numpy as np

from .vad_service import VADService
from .antispoof import AntiSpoofDetector
from .prosody_service import ProsodyService
from .paralinguistic_service import ParalinguisticService
from .speaker_verification import SpeakerVerifier
from .risk_scoring import combine_layer_results

try:
    from .telephone_channel import TelephoneChannelPreprocessor
except ImportError:
    TelephoneChannelPreprocessor = None

logger = logging.getLogger(__name__)


class StreamSession:
    """
    Stateful per-connection object for streaming deepfake analysis.

    Lifecycle:
        session = StreamSession(mode="phone")  # or "normal"
        result = await session.process_chunk(raw_pcm_bytes)
        # result is None for silence frames, a verdict dict otherwise
        session.cleanup()  # call on disconnect
    """

    # How many seconds of audio to buffer (circular)
    BUFFER_SECONDS = 10
    # Minimum seconds of audio needed before running first analysis (1.0s)
    MIN_ANALYSIS_SECONDS = 1.0
    # How many samples per analysis window (1.0s)
    WINDOW_SECONDS = 1.0
    # Minimum interval between successive analyses (0.5s cadence)
    CADENCE_SECONDS = 0.5
    # Minimum seconds in buffer before kicking off async watermark check
    WATERMARK_TRIGGER_SECONDS = 7
    # How many F0 values to track for running CV computation
    PITCH_HISTORY_LEN = 100

    def __init__(self, sample_rate: int = 16000, mode: str = "normal") -> None:
        self.sample_rate = sample_rate
        self.mode = mode.lower()
        self._buffer: deque[int] = deque(
            maxlen=self.BUFFER_SECONDS * sample_rate
        )
        self._vad = VADService(aggressiveness=2, sample_rate=sample_rate, frame_ms=30)
        self._frame_samples = self._vad.frame_samples

        # Telephony channel preprocessor
        self._preprocessor = (
            TelephoneChannelPreprocessor(target_sr=sample_rate)
            if TelephoneChannelPreprocessor is not None
            else None
        )
        self.is_telephony: bool = (self.mode == "phone" or sample_rate <= 8000)

        # Running layer state
        self._pitch_history: deque[float] = deque(maxlen=self.PITCH_HISTORY_LEN)
        self._first_embedding: Optional[np.ndarray] = None  # for speaker consistency
        self._last_analysis_samples: int = 0
        self._smoothed_authenticity: Optional[float] = None

        # Layer service instances (one per session, not one per chunk)
        self._antispoof = AntiSpoofDetector()
        self._prosody = ProsodyService()
        self._paralinguistic = ParalinguisticService()
        self._speaker = SpeakerVerifier()

        # Async Layer 6 watermark task
        self._watermark_task: Optional[asyncio.Task] = None
        self._last_watermark_result: Optional[Dict[str, Any]] = None

        # Async Layer 5 semantic task
        self._semantic_task: Optional[asyncio.Task] = None
        self._last_semantic_result: Optional[Dict[str, Any]] = None
        self._pending_segment: Optional[np.ndarray] = None  # VAD-gated segment for Whisper

        # Total samples received (for RTF measurement)
        self.total_samples_received: int = 0

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def process_chunk(self, chunk: bytes) -> Optional[Dict[str, Any]]:
        """
        Ingest a raw PCM chunk and return a verdict dict if analysis ran,
        or None if the frame was silence / buffer too short.

        Args:
            chunk: Raw bytes, 16-bit signed PCM, mono, at self.sample_rate.
                   Must be exactly one VAD frame (30ms = 960 samples = 1920 bytes).

        Returns:
            Dict with layer scores + combined verdict, or None.
        """
        # Convert bytes → int16 array
        try:
            samples = np.frombuffer(chunk, dtype=np.int16)
        except Exception as exc:
            logger.warning("StreamSession: failed to decode chunk bytes: %s", exc)
            return None

        self.total_samples_received += len(samples)
        self._buffer.extend(samples.tolist())

        # Gate on VAD — skip silence
        if not self._vad.is_speech_bytes(chunk):
            return None

        # Accumulate speech samples for async Whisper
        self._accumulate_segment(samples)

        # Need at least MIN_ANALYSIS_SECONDS before running layers
        if len(self._buffer) < int(self.MIN_ANALYSIS_SECONDS * self.sample_rate):
            return None

        # Stride / Cadence: ensure at least CADENCE_SECONDS has elapsed since last analysis
        if self._last_analysis_samples > 0:
            samples_since_last = self.total_samples_received - self._last_analysis_samples
            if samples_since_last < int(self.CADENCE_SECONDS * self.sample_rate):
                return None

        self._last_analysis_samples = self.total_samples_received

        # Grab analysis window (last WINDOW_SECONDS or all available)
        window_len = min(len(self._buffer), int(self.WINDOW_SECONDS * self.sample_rate))
        window = np.array(list(self._buffer)[-window_len:], dtype=np.int16)
        # Normalise to float32 [-1, 1] for librosa
        window_f32 = window.astype(np.float32) / 32768.0

        # Apply telephone channel preprocessing (bandwidth detection + Wiener denoise)
        if self._preprocessor is not None:
            window_f32, _, tele_meta = self._preprocessor.preprocess(
                window_f32, self.sample_rate, denoise=True
            )
            if tele_meta.get("is_telephony", False):
                self.is_telephony = True

        # Trigger async watermark check if buffer is long enough and not phone channel
        if not self.is_telephony:
            self._maybe_trigger_watermark()

        # Run fast layers synchronously (they're already fast with array API)
        layer_results, weights = self._run_fast_layers(window_f32)

        # Merge async results from previous watermark / semantic runs
        self._merge_async_results(layer_results, weights)

        # Adjust layer weights dynamically for telephone bandwidth
        if self.is_telephony and self._preprocessor is not None:
            weights = self._preprocessor.adjust_layer_weights(weights, is_telephony=True)
            if "layer6_watermark" in layer_results:
                layer_results["layer6_watermark"]["status"] = "disabled_telephony"

        # Score
        verdict = combine_layer_results(layer_results, weights)

        # Temporal smoothing (EMA): 500ms cadence uses 0.50/0.50 for agility
        raw_score = verdict["overall_authenticity_score"]
        watermark_found = layer_results.get("layer6_watermark", {}).get("found", False)
        if watermark_found:
            smoothed = 0.0
        elif self._smoothed_authenticity is None:
            smoothed = raw_score
        else:
            smoothed = round(0.50 * raw_score + 0.50 * self._smoothed_authenticity, 4)

        self._smoothed_authenticity = smoothed
        verdict["overall_authenticity_score"] = smoothed

        open_source_model = layer_results.get("layer1_antispoof", {}).get(
            "open_source_model", {}
        )
        model_fake_probability = open_source_model.get("fake_probability")
        high_confidence_model_fake = (
            isinstance(model_fake_probability, (int, float))
            and model_fake_probability >= 0.85
        )

        if high_confidence_model_fake:
            verdict["overall_authenticity_score"] = min(smoothed, 0.25)
            verdict["verdict"] = "Deepfake (Open-Source Model)"
            verdict["is_authentic"] = False
        elif not watermark_found:
            if smoothed > 0.8:
                verdict["verdict"] = "Authentic (Human)"
            elif smoothed > 0.6:
                verdict["verdict"] = "Likely Human"
            elif smoothed > 0.4:
                verdict["verdict"] = "Unverified / Insufficient Evidence"
            elif smoothed > 0.2:
                verdict["verdict"] = "Suspicious (Likely Synthetic)"
            else:
                verdict["verdict"] = "Deepfake (Synthetic)"
            verdict["is_authentic"] = bool(smoothed > 0.5)

        # 500ms Cadence & Partial Fake Localization Metadata
        window_start_s = round(max(0.0, (self.total_samples_received - window_len) / self.sample_rate), 2)
        window_end_s = round(self.total_samples_received / self.sample_rate, 2)

        verdict["buffer_seconds"] = round(window_len / self.sample_rate, 2)
        verdict["samples_processed"] = self.total_samples_received
        verdict["cadence_ms"] = 500
        verdict["window_start_s"] = window_start_s
        verdict["window_end_s"] = window_end_s
        verdict["is_telephony"] = self.is_telephony
        verdict["segment_label"] = "REAL" if smoothed >= 0.5 else "FAKE"

        return verdict

    def cleanup(self) -> None:
        """Cancel background tasks on WebSocket disconnect."""
        for task in [self._watermark_task, self._semantic_task]:
            if task and not task.done():
                task.cancel()

    # ------------------------------------------------------------------
    # Fast-path layer execution (Layers 1, 3, 4, 2-consistency)
    # ------------------------------------------------------------------

    def _run_fast_layers(
        self, window_f32: np.ndarray
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        results: Dict[str, Any] = {}
        weights: Dict[str, Any] = {}

        # Layer 1: Anti-Spoof
        try:
            antispoof = self._antispoof.detect_array(window_f32, self.sample_rate)
            auth_l1 = max(0.0, 1.0 - antispoof.get("spoof_score", 0.5))
            antispoof["score"] = round(auth_l1, 4)
            results["layer1_antispoof"] = antispoof
            weights["l1"] = {"score": auth_l1, "weight": 0.35}
        except Exception as exc:
            results["layer1_antispoof"] = {"error": str(exc)}

        # Layer 3: Prosody
        try:
            prosody = self._prosody.analyse_array(window_f32, self.sample_rate)
            auth_l3 = prosody.get("authenticity_score", 0.5)
            # Update running pitch history for CV tracking
            if prosody.get("f0_mean_hz") is not None:
                self._pitch_history.append(prosody["f0_mean_hz"])
            prosody["score"] = round(auth_l3, 4)
            results["layer3_prosody"] = prosody
            weights["l3"] = {"score": auth_l3, "weight": 0.15}
        except Exception as exc:
            results["layer3_prosody"] = {"error": str(exc)}

        # Layer 4: Paralinguistic
        try:
            para = self._paralinguistic.analyse_array(window_f32, self.sample_rate)
            auth_l4 = para.get("authenticity_score", 0.5)
            para["score"] = round(auth_l4, 4)
            results["layer4_paralinguistic"] = para
            weights["l4"] = {"score": auth_l4, "weight": 0.10}
        except Exception as exc:
            results["layer4_paralinguistic"] = {"error": str(exc)}

        # Layer 2: Speaker consistency (embedding drift detection)
        try:
            embedding = self._speaker.embed_array(window_f32, self.sample_rate)
            if self._first_embedding is None:
                self._first_embedding = embedding
                auth_l2 = 1.0  # neutral on first window
            else:
                score = float(np.dot(embedding, self._first_embedding))
                auth_l2 = float(np.clip(score, 0.0, 1.0))
            results["layer2_speaker_consistency"] = {
                "score": round(auth_l2, 4),
                "engine": "mfcc_cosine_drift",
            }
            weights["l2"] = {"score": auth_l2, "weight": 0.15}
        except Exception as exc:
            results["layer2_speaker_consistency"] = {"error": str(exc)}

        return results, weights

    # ------------------------------------------------------------------
    # Async watermark (Layer 6)
    # ------------------------------------------------------------------

    def _maybe_trigger_watermark(self) -> None:
        trigger = int(self.WATERMARK_TRIGGER_SECONDS * self.sample_rate)
        if len(self._buffer) >= trigger and self._watermark_task is None:
            audio_snapshot = np.array(list(self._buffer), dtype=np.int16)
            self._watermark_task = asyncio.create_task(
                self._check_watermark(audio_snapshot)
            )

    async def _check_watermark(self, audio: np.ndarray) -> None:
        try:
            from ..core.watermark import WatermarkService
            service = WatermarkService()
            result = await service.detect_watermark_array(audio, self.sample_rate)
            self._last_watermark_result = result
        except Exception as exc:
            logger.warning("StreamSession: watermark check failed: %s", exc)
            self._last_watermark_result = {"error": str(exc)}
        finally:
            self._watermark_task = None  # allow next trigger

    # ------------------------------------------------------------------
    # Async Whisper (Layer 5)
    # ------------------------------------------------------------------

    def _accumulate_segment(self, samples: np.ndarray) -> None:
        """Accumulate samples for Whisper; launch task when we have >=3s."""
        if self._pending_segment is None:
            self._pending_segment = samples
        else:
            self._pending_segment = np.concatenate([self._pending_segment, samples])

        segment_secs = len(self._pending_segment) / self.sample_rate
        if segment_secs >= 3.0 and self._semantic_task is None:
            segment = self._pending_segment.copy()
            self._pending_segment = None
            self._semantic_task = asyncio.create_task(
                self._check_semantic(segment)
            )

    async def _check_semantic(self, audio: np.ndarray) -> None:
        try:
            from .semantic_service import SemanticService
            svc = SemanticService()
            audio_f32 = audio.astype(np.float32) / 32768.0
            
            # Use asyncio.to_thread to prevent blocking the event loop
            # with synchronous Whisper transcription
            result = await asyncio.to_thread(svc.analyse_segment, audio_f32, self.sample_rate)
            
            self._last_semantic_result = result
        except Exception as exc:
            logger.warning("StreamSession: semantic check failed: %s", exc)
            self._last_semantic_result = {"error": str(exc)}
        finally:
            self._semantic_task = None

    # ------------------------------------------------------------------
    # Merge async results into current verdict
    # ------------------------------------------------------------------

    def _merge_async_results(
        self,
        layer_results: Dict[str, Any],
        weights: Dict[str, Any],
    ) -> None:
        """Inject the most recent watermark and semantic results, if available."""
        if self._last_watermark_result is not None:
            wm = dict(self._last_watermark_result)
            auth_l6 = 0.0 if wm.get("found", False) else 1.0
            wm["score"] = round(auth_l6, 4)
            wm["verdict"] = "Watermark Detected" if wm.get("found") else "Clean"
            layer_results["layer6_watermark"] = wm
            weights["l6"] = {"score": auth_l6, "weight": 0.20}

        if self._last_semantic_result is not None:
            sem = dict(self._last_semantic_result)
            auth_l5 = sem.get("authenticity_score", 0.5)
            sem["score"] = round(auth_l5, 4)
            layer_results["layer5_semantic"] = sem
            weights["l5"] = {"score": auth_l5, "weight": 0.20}
