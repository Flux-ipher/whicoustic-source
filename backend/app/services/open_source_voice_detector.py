"""Open-source AI voice detector backed by a Hugging Face audio classifier."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


class OpenSourceVoiceDetector:
    """Lazy Wav2Vec2 detector for synthetic speech.

    The model is deliberately loaded on first inference so API startup does not
    depend on Hugging Face availability. Model failures are surfaced to the
    caller as an unavailable result and never masquerade as human speech.
    """

    DEFAULT_MODEL_ID = "Bgeorge/deepfake-audio-detector-wav2vec2"
    SAMPLE_RATE = 16000
    WINDOW_SAMPLES = 16000
    HOP_SAMPLES = 8000

    def __init__(self, model_id: Optional[str] = None) -> None:
        self.model_id = model_id or os.getenv(
            "AI_VOICE_DETECTOR_MODEL", self.DEFAULT_MODEL_ID
        )
        self._processor: Any = None
        self._model: Any = None
        self._device: Any = None
        self._load_error: Optional[str] = None

    def _load(self) -> None:
        if self._processor is not None and self._model is not None:
            return
        if self._load_error is not None:
            raise RuntimeError(self._load_error)

        try:
            import torch
            from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

            self._device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )
            self._processor = AutoFeatureExtractor.from_pretrained(self.model_id)
            self._model = AutoModelForAudioClassification.from_pretrained(
                self.model_id
            ).to(self._device)
            self._model.eval()
            logger.info(
                "Loaded open-source AI voice detector %s on %s",
                self.model_id,
                self._device,
            )
        except Exception as exc:
            self._load_error = (
                f"Could not load open-source voice detector "
                f"{self.model_id}: {exc}"
            )
            logger.error(self._load_error)
            raise RuntimeError(self._load_error) from exc

    def _fake_index(self) -> int:
        labels = getattr(getattr(self._model, "config", None), "id2label", {}) or {}
        for index, label in labels.items():
            if any(term in str(label).lower() for term in ("fake", "spoof", "deepfake")):
                return int(index)
        return 1

    def detect(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Return fake probability aggregated over overlapping one-second windows."""
        import librosa

        self._load()
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=-1)
        if sample_rate != self.SAMPLE_RATE:
            audio = librosa.resample(
                audio, orig_sr=sample_rate, target_sr=self.SAMPLE_RATE
            )
        if audio.size == 0:
            raise ValueError("Audio is empty")

        if audio.size <= self.WINDOW_SAMPLES:
            starts = [0]
        else:
            last_start = audio.size - self.WINDOW_SAMPLES
            starts = list(range(0, last_start + 1, self.HOP_SAMPLES))
            if starts[-1] != last_start:
                starts.append(last_start)

        import torch

        fake_index = self._fake_index()
        fake_scores = []
        with torch.inference_mode():
            for start in starts:
                window = audio[start : start + self.WINDOW_SAMPLES]
                if window.size < self.WINDOW_SAMPLES:
                    window = np.pad(window, (0, self.WINDOW_SAMPLES - window.size))
                inputs = self._processor(
                    window,
                    sampling_rate=self.SAMPLE_RATE,
                    max_length=self.WINDOW_SAMPLES,
                    truncation=True,
                    padding="max_length",
                    return_tensors="pt",
                )
                inputs = {
                    key: value.to(self._device) for key, value in inputs.items()
                }
                logits = self._model(**inputs).logits
                probabilities = torch.softmax(logits, dim=-1)[0]
                fake_scores.append(float(probabilities[fake_index].item()))

        mean_fake = float(np.mean(fake_scores))
        peak_fake = float(np.max(fake_scores))
        # A high-confidence window is useful for catching short synthetic
        # segments, while the mean limits one noisy frame's influence.
        fake_probability = float(np.clip(0.7 * peak_fake + 0.3 * mean_fake, 0.0, 1.0))
        return {
            "fake_probability": round(fake_probability, 4),
            "mean_fake_probability": round(mean_fake, 4),
            "peak_fake_probability": round(peak_fake, 4),
            "windows_evaluated": len(fake_scores),
            "model_id": self.model_id,
            "engine": "huggingface_wav2vec2",
        }

