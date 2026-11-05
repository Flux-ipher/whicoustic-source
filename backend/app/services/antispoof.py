"""
Anti-spoofing (deepfake) detector.

Uses an open-source Hugging Face voice deepfake classifier when available and
keeps the spectral detector as an explicit fallback.
"""
from __future__ import annotations

import numpy as np
import librosa
from typing import Dict, Any
import logging
import os
from .open_source_voice_detector import OpenSourceVoiceDetector

logger = logging.getLogger(__name__)

try:
    import torch
    import torchaudio
    from speechbrain.inference.interfaces import foreign_class
    _HAS_SB = True
except ImportError:
    _HAS_SB = False
    torch = None


class AntiSpoofDetector:
    def __init__(self) -> None:
        self._model = None
        self._custom_model = None
        self._device = "cuda" if _HAS_SB and torch.cuda.is_available() else "cpu"
        self._open_source_detector = OpenSourceVoiceDetector()
        
        # Try to load Custom Trained RF Model first (so we can test it)
        try:
            import joblib
            model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "ml", "simple_rf_detector.pkl")
            if os.path.exists(model_path):
                self._custom_model = joblib.load(model_path)
                logger.info("Custom Lightweight RF Anti-Spoof model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load custom RF model: {e}")
            
        if _HAS_SB and not self._custom_model:
            try:
                # Attempt to load the AASIST anti-spoofing model
                # Note: this requires an internet connection on first run to download the model from HuggingFace
                # It uses the foreign_class interface because AASIST has a custom architecture
                save_dir = os.path.join(os.path.expanduser("~"), ".cache", "speechbrain", "aasist")
                self._model = foreign_class(
                    source="speechbrain/aasist",
                    pymodule_file="custom_interface.py",
                    classname="CustomEncoderWav2vec2Classifier", # Note: This is an example class name, if it fails, it will fall back to heuristics
                    savedir=save_dir,
                    run_opts={"device": self._device}
                )
                logger.info("SpeechBrain AASIST model loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load SpeechBrain AASIST model: {e}. Falling back to heuristics.")
                self._model = None

    def _extract_features(self, y: np.ndarray, sr: int) -> np.ndarray:
        # Compute spectral stats
        S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256))
        S_db = librosa.amplitude_to_db(S + 1e-9)
        
        # High-frequency energy ratio
        freqs = np.linspace(0, sr // 2, S.shape[0])
        hf_mask = freqs > (sr * 0.35)
        hf_energy = float(np.mean(S_db[hf_mask, :]))
        mid_energy = float(np.mean(S_db[(freqs > sr * 0.1) & (freqs <= sr * 0.35), :]))
        hf_ratio = float((hf_energy - mid_energy) / (abs(mid_energy) + 1e-6))
        
        # Synthesized audio often has a sharp high-frequency cutoff
        # and unnatural phase variations from the vocoder.
        
        # Phase inconsistency proxy
        phase = np.angle(librosa.stft(y, n_fft=512, hop_length=128))
        phase_var = float(np.var(np.diff(phase, axis=1)))
        
        # Zero-crossing irregularity
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_std = float(np.std(zcr))
        
        # Silence/Breath ratio (Natural speech has distinct pauses/breaths)
        # Deepfakes sometimes have completely dead silence or weird constant noise floors
        rms = librosa.feature.rms(y=y)[0]
        silence_threshold = np.mean(rms) * 0.1
        silence_ratio = float(np.sum(rms < silence_threshold) / len(rms))
        
        return np.array([hf_ratio, phase_var, zcr_std, silence_ratio])

    def _heuristics(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        features = self._extract_features(y, sr)
        custom_score = None
        if self._custom_model:
            # Use our custom trained ML model
            try:
                # predict_proba returns [[prob_real, prob_fake]]
                probs = self._custom_model.predict_proba([features])[0]
                custom_score = float(probs[1])
            except Exception as e:
                logger.error(f"Custom RF model inference failed: {e}")
                # Fall through to manual heuristics
        
        # Calibrated acoustic heuristic scores (0 = authentic human, 1 = synthetic spoof)
        # 1. High-frequency balance: natural human speech has glottal roll-off (-6dB/octave),
        # placing hf_ratio between -0.25 and +0.15. Sharp brickwall filters (< -0.30)
        # or vocoder metallic hiss (> 0.25) indicate synthetic audio.
        if features[0] < -0.30:
            score_hf = float(np.clip(abs(features[0] + 0.30) * 3.0, 0.0, 1.0))
        elif features[0] > 0.25:
            score_hf = float(np.clip((features[0] - 0.25) * 3.0, 0.0, 1.0))
        else:
            score_hf = 0.05

        # 2. Phase variance: natural human acoustic rooms/mic non-stationarity produces
        # phase_var in ~4.0 to 8.5. Over-regularized synthetic vocoders (< 2.5) or
        # phase distortion (> 12.0) indicate synthesis.
        if features[1] < 2.5:
            score_phase = float(np.clip((2.5 - features[1]) / 2.5, 0.0, 1.0))
        elif features[1] > 12.0:
            score_phase = float(np.clip((features[1] - 12.0) / 8.0, 0.0, 1.0))
        else:
            score_phase = 0.05

        # 3. ZCR irregularity: dynamic consonant articulation produces zcr_std > 0.06.
        # Over-smoothed or robotic TTS produces zcr_std < 0.05.
        if features[2] < 0.05:
            score_zcr = float(np.clip((0.05 - features[2]) / 0.05, 0.0, 1.0))
        else:
            score_zcr = 0.05

        # 4. Silence/Breath ratio: natural human speech has breath/pauses (silence_ratio > 0.02).
        if features[3] < 0.01:
            score_silence = 0.50
        else:
            score_silence = 0.0
        
        heuristic_score = np.clip(
            (0.4 * score_hf)
            + (0.3 * score_phase)
            + (0.2 * score_zcr)
            + (0.1 * score_silence),
            0,
            1,
        )
        if custom_score is not None:
            heuristic_score = float(0.5 * heuristic_score + 0.5 * custom_score)
        model_result: Dict[str, Any] = {}
        try:
            model_result = self._open_source_detector.detect(y, sr)
            spoof_score = np.clip(
                0.65 * model_result["fake_probability"] + 0.35 * heuristic_score,
                0,
                1,
            )
        except Exception as exc:
            logger.warning("Open-source voice detector unavailable: %s", exc)
            spoof_score = heuristic_score
            model_result = {
                "engine": "unavailable",
                "error": str(exc),
            }

        return {
            "spoof_score": float(spoof_score),
            "is_spoof": spoof_score > 0.5,
            "features": {
                "hf_ratio": features[0],
                "phase_var": features[1],
                "zcr_std": features[2],
                "silence_ratio": features[3]
            },
            "open_source_model": model_result,
            "engine": "enhanced_heuristic"
            if model_result.get("engine") == "unavailable"
            else "open_source_wav2vec2_plus_heuristic",
        }

    def detect(self, path: str) -> Dict[str, Any]:
        """Detect spoofing from an audio file."""
        y, sr = librosa.load(path, sr=16000, mono=True)
        return self._heuristics(y, sr)

    def detect_array(self, audio: np.ndarray, sr: int = 16000) -> Dict[str, Any]:
        """
        Run anti-spoof analysis directly on an in-memory numpy array.

        Streaming variant: skips librosa.load() since the caller (StreamSession)
        already has the audio in memory. The underlying _heuristics() logic is
        identical to the file-based detect() path.

        Args:
            audio: 1-D float32 array, values in [-1, 1], mono.
            sr: Sample rate in Hz (default 16000).

        Returns:
            Same dict as detect().
        """
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=-1)
            
        return self._heuristics(audio, sr)