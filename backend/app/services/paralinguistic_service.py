"""
Paralinguistic / Emotion Coherence Service — Layer 4 of the 6-layer defense pipeline.

Analyses the acoustic features (MFCC, spectral contrast, energy) to extract a rough
emotional valence/arousal profile, and compares it against expected natural speech variance.
In a full production environment, this would use a speech-emotion-recognition (SER) model 
(like wav2vec2-emotion) paired with semantic sentiment analysis to detect tone/content mismatch.
For this MVP, we analyze energetic variance (arousal) to detect "flat delivery".

Synthetic audio tends to be emotionally flat or have a mismatched energy profile compared 
to human speech which naturally varies significantly.
"""
from __future__ import annotations

import librosa
import numpy as np
from typing import Dict, Any


try:
    import torch
    import torchaudio
    from speechbrain.inference.interfaces import foreign_class
    _HAS_SB = True
except ImportError:
    _HAS_SB = False
    torch = None

import logging
logger = logging.getLogger(__name__)

class ParalinguisticService:
    """Layer 4: Paralinguistic Coherence analyser."""

    def __init__(self) -> None:
        self._model = None
        self._device = "cuda" if _HAS_SB and torch.cuda.is_available() else "cpu"
        
        if _HAS_SB:
            try:
                import os
                save_dir = os.path.join(os.path.expanduser("~"), ".cache", "speechbrain", "emotion")
                self._model = foreign_class(
                    source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
                    pymodule_file="custom_interface.py",
                    classname="CustomEncoderWav2vec2Classifier",
                    savedir=save_dir,
                    run_opts={"device": self._device}
                )
                logger.info("SpeechBrain Emotion Recognition model loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load SpeechBrain Emotion model: {e}. Falling back to heuristics.")
                self._model = None

    def analyse(self, audio_path: str) -> Dict[str, Any]:
        """Run paralinguistic analysis on an audio file.

        Args:
            audio_path: Path to a WAV/FLAC/MP3 file.

        Returns:
            Dict with:
              - authenticity_score (float, 0–1, higher = more natural)
              - arousal_variance (float)
              - spectral_contrast_std (float)
              - engine (str)
        """
        try:
            y, sr = librosa.load(audio_path, sr=16000, mono=True)
            return self._analyse_waveform(y, sr)
        except Exception as exc:
            return {
                "authenticity_score": 0.5,
                "error": str(exc),
                "engine": "paralinguistic_heuristic",
            }

    def analyse_array(self, audio: np.ndarray, sr: int = 16000) -> Dict[str, Any]:
        """
        Run paralinguistic analysis directly on an in-memory numpy array.

        Streaming variant: skips librosa.load() since StreamSession already
        has the audio in memory. Delegates to the same _analyse_waveform()
        used by the file-based path.

        Args:
            audio: 1-D float32 array, values in [-1, 1], mono.
            sr: Sample rate in Hz (default 16000).

        Returns:
            Same dict as analyse().
        """
        try:
            audio = np.asarray(audio, dtype=np.float32)
            if audio.ndim > 1:
                audio = np.mean(audio, axis=-1)
            return self._analyse_waveform(audio, sr)
        except Exception as exc:
            return {
                "authenticity_score": 0.5,
                "error": str(exc),
                "engine": "paralinguistic_heuristic",
            }


    def _analyse_waveform(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        # Optional: SER model inference
        emotion_features = {}
        if self._model is not None and _HAS_SB:
            try:
                # Convert to tensor and resample if needed
                signal = torch.from_numpy(y).unsqueeze(0).to(torch.float32)
                if sr != 16000:
                    resampler = torchaudio.transforms.Resample(sr, 16000)
                    signal = resampler(signal)
                signal = signal.to(self._device)
                
                # Inference
                out_prob, score, index, text_lab = self._model.classify_batch(signal)
                emotion = text_lab[0]
                
                # Synthesized audio often comes out as "neu" (neutral) 
                # highly confident neutral delivery without variation is a deepfake signal.
                emotion_features = {
                    "emotion": emotion,
                    "neutral_confidence": float(out_prob[0][0].item()) # IEMOCAP labels vary, index 0 is often neu
                }
            except Exception as e:
                logger.warning(f"SER inference failed: {e}")
        # 1. Arousal Variance (Energy/RMS fluctuations)
        # Humans naturally vary their volume/energy when speaking (prosodic stress).
        # TTS is often normalized and flat.
        rms = librosa.feature.rms(y=y)[0]
        # Ignore complete silence to focus on speech energy
        speech_rms = rms[rms > (np.mean(rms) * 0.1)]
        
        if len(speech_rms) < 10:
            return {
                "authenticity_score": 0.5,
                "error": "Not enough speech for paralinguistic analysis",
                "engine": "paralinguistic_heuristic",
            }

        arousal_variance = float(np.std(speech_rms) / (np.mean(speech_rms) + 1e-6))
        
        # 2. Spectral Contrast Variance
        # Spectral contrast represents the difference in amplitude between peaks and valleys.
        # High variation means dynamic articulation; low means robotic/flat.
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        contrast_std = float(np.mean(np.std(contrast, axis=1)))

        # Natural speech arousal CV is typically 0.35 - 0.70+.
        # Calm audiobook narration sits around 0.35 - 0.52.
        # Flat robotic / synthetic TTS is usually < 0.22.
        if arousal_variance >= 0.45:
            arousal_score = float(np.clip(0.95 + 0.05 * min(1.0, (arousal_variance - 0.45) / 0.15), 0.0, 1.0))
        elif arousal_variance >= 0.32:
            arousal_score = float(0.85 + 0.10 * ((arousal_variance - 0.32) / 0.13))
        elif arousal_variance >= 0.22:
            arousal_score = float(0.40 + 0.45 * ((arousal_variance - 0.22) / 0.10))
        else:
            arousal_score = float(max(0.0, (arousal_variance / 0.22) * 0.40))
        
        # Spectral contrast std typically > 3.0 for natural speech
        contrast_score = float(np.clip((contrast_std - 2.0) / 2.0, 0.0, 1.0))

        # Authenticity score combining arousal dynamics and spectral contrast
        authenticity_score = float(0.50 * arousal_score + 0.50 * contrast_score)

        return {
            "authenticity_score": round(authenticity_score, 4),
            "arousal_variance": round(arousal_variance, 4),
            "spectral_contrast_std": round(contrast_std, 4),
            "engine": "speechbrain_emotion" if emotion_features else "paralinguistic_heuristic",
            "details": {
                "arousal_score": round(float(arousal_score), 4),
                "contrast_score": round(float(contrast_score), 4),
                **emotion_features
            }
        }
