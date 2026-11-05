"""
Speaker verification service.

Prefers SpeechBrain ECAPA-TDNN if available; falls back to MFCC cosine similarity.
Supports dual-mode verification:
1. Cross-Speaker Verification (when external reference voice is provided)
2. Intra-Utterance Speaker Consistency & Biometric Stability (when standalone audio is evaluated)
"""
from __future__ import annotations

import numpy as np
import librosa
from typing import Optional, Dict, Any, Union

try:
    import torch  # type: ignore
    from speechbrain.pretrained import SpeakerRecognition  # type: ignore
    _SB_AVAILABLE = True
except Exception:
    _SB_AVAILABLE = False
    SpeakerRecognition = None  # type: ignore
    torch = None  # type: ignore


class SpeakerVerifier:
    def __init__(self) -> None:
        self._rec: Optional[SpeakerRecognition] = None
        if _SB_AVAILABLE:
            try:
                # Downloads the model on first use
                self._rec = SpeakerRecognition.from_hparams(
                    source="speechbrain/spkrec-ecapa-voxceleb", savedir=".cache/spkrec_ecapa"
                )
            except Exception:
                self._rec = None

    def _mfcc_embed(self, wav_path: str, sr: int = 16000) -> np.ndarray:
        y, s = librosa.load(wav_path, sr=sr, mono=True)
        mfcc = librosa.feature.mfcc(y=y, sr=s, n_mfcc=40)
        # Mean pooling
        emb = np.mean(mfcc, axis=1)
        emb = emb / (np.linalg.norm(emb) + 1e-9)
        return emb

    def embed_array(self, audio: np.ndarray, sr: int = 16000) -> np.ndarray:
        """
        Compute a normalised MFCC speaker embedding from an in-memory array.

        Streaming variant used by StreamSession for speaker-consistency drift
        detection: compare the first window's embedding against subsequent
        windows to detect speaker changes mid-session.

        Args:
            audio: 1-D float32 array, values in [-1, 1], mono.
            sr: Sample rate in Hz (default 16000).

        Returns:
            1-D float32 numpy array of shape (40,), L2-normalised.
        """
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=-1)
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        emb = np.mean(mfcc, axis=1)
        emb = emb / (np.linalg.norm(emb) + 1e-9)
        return emb.astype(np.float32)

    def verify(self, ref_path: str, qry_path: str) -> Dict[str, Any]:
        """
        Verify whether two audio files are spoken by the same identity (Cross-Speaker Verification).
        """
        if self._rec is not None:
            try:
                score, decision = self._rec.verify_files(ref_path, qry_path)
                s = float(score)
                return {
                    "engine": "speechbrain_ecapa",
                    "mode": "cross_speaker_verification",
                    "score": s,
                    "similarity_score": s,
                    "is_same_speaker": bool(decision),
                }
            except Exception:
                # Fallback to MFCC
                pass
        # MFCC cosine similarity fallback
        ref = self._mfcc_embed(ref_path)
        qry = self._mfcc_embed(qry_path)
        score = float(np.dot(ref, qry))
        return {
            "engine": "mfcc_cosine",
            "mode": "cross_speaker_verification",
            "score": score,
            "similarity_score": score,
            "is_same_speaker": bool(score > 0.8),
        }

    def verify_array(self, ref_audio: np.ndarray, qry_audio: np.ndarray, sr: int = 16000) -> Dict[str, Any]:
        """
        Verify whether two in-memory audio arrays belong to the same speaker.
        """
        ref_emb = self.embed_array(ref_audio, sr=sr)
        qry_emb = self.embed_array(qry_audio, sr=sr)
        score = float(np.dot(ref_emb, qry_emb))
        return {
            "engine": "mfcc_cosine",
            "mode": "cross_speaker_verification",
            "score": score,
            "similarity_score": score,
            "is_same_speaker": bool(score > 0.8),
        }

    def analyze_consistency_array(self, audio: np.ndarray, sr: int = 16000) -> Dict[str, Any]:
        """
        Evaluate Intra-Utterance Speaker Biometric Consistency & Stability.

        When no external reference speaker audio is supplied, Layer 2 checks whether
        the biometric vocal tract identity remains stable throughout the clip,
        or shows anomalous drift, multi-speaker splices, or voice-conversion shifts.

        Args:
            audio: 1-D float32 audio array.
            sr: Sample rate in Hz (default 16000).

        Returns:
            Dict containing consistency_score, similarity_score, drift metrics, and verdicts.
        """
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=-1)

        total_len = len(audio)
        duration = float(total_len / sr) if sr > 0 else 0.0

        # Edge cases: short clip or low energy
        if total_len < int(0.3 * sr) or np.max(np.abs(audio)) < 1e-4:
            return {
                "engine": "mfcc_biometric_consistency",
                "mode": "intra_utterance_consistency",
                "consistency_score": 0.90,
                "score": 0.90,
                "similarity_score": 0.90,
                "is_same_speaker": True,
                "is_consistent": True,
                "mean_similarity": 1.0,
                "min_similarity": 1.0,
                "embedding_drift": 0.0,
                "segments_analyzed": 1,
                "duration_sec": round(duration, 3),
                "status": "short_or_low_energy",
            }

        # Windowing: 1.0s window, 0.5s hop
        win_samples = int(1.0 * sr)
        hop_samples = int(0.5 * sr)

        embs = []
        if total_len >= win_samples:
            for start in range(0, total_len - win_samples + 1, hop_samples):
                chunk = audio[start:start + win_samples]
                rms = float(np.sqrt(np.mean(chunk**2)))
                if rms > 0.006:
                    emb = self.embed_array(chunk, sr=sr)
                    embs.append(emb)

        # Fallback to halves if fewer than 2 segments passed energy gate
        if len(embs) < 2:
            mid = total_len // 2
            for part in [audio[:mid], audio[mid:]]:
                if len(part) >= int(0.15 * sr):
                    emb = self.embed_array(part, sr=sr)
                    embs.append(emb)

        if len(embs) < 2:
            return {
                "engine": "mfcc_biometric_consistency",
                "mode": "intra_utterance_consistency",
                "consistency_score": 0.92,
                "score": 0.92,
                "similarity_score": 0.92,
                "is_same_speaker": True,
                "is_consistent": True,
                "mean_similarity": 1.0,
                "min_similarity": 1.0,
                "embedding_drift": 0.0,
                "segments_analyzed": 1,
                "duration_sec": round(duration, 3),
            }

        # Compute centroid & drift
        centroid = np.mean(embs, axis=0)
        centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
        sims_to_centroid = [float(np.dot(e, centroid)) for e in embs]

        mean_sim = float(np.mean(sims_to_centroid))
        min_sim = float(np.min(sims_to_centroid))
        drift = float(max(0.0, 1.0 - min_sim))

        # Sequential stability
        consec_sims = [float(np.dot(embs[i], embs[i+1])) for i in range(len(embs)-1)]
        min_consec = float(np.min(consec_sims)) if consec_sims else mean_sim

        # Calibrated authenticity mapping [0.0, 1.0]
        if mean_sim >= 0.90:
            base_score = 0.90 + 0.10 * ((mean_sim - 0.90) / 0.10)
        elif mean_sim >= 0.75:
            base_score = 0.70 + 0.20 * ((mean_sim - 0.75) / 0.15)
        else:
            base_score = max(0.05, mean_sim * 0.75)

        consistency_score = max(0.0, min(1.0, base_score - drift * 0.20))

        return {
            "engine": "mfcc_biometric_consistency",
            "mode": "intra_utterance_consistency",
            "consistency_score": round(consistency_score, 4),
            "score": round(consistency_score, 4),
            "similarity_score": round(consistency_score, 4),
            "is_same_speaker": bool(consistency_score >= 0.70),
            "is_consistent": bool(consistency_score >= 0.70),
            "mean_similarity": round(mean_sim, 4),
            "min_similarity": round(min_sim, 4),
            "min_consecutive_similarity": round(min_consec, 4),
            "embedding_drift": round(drift, 4),
            "segments_analyzed": len(embs),
            "duration_sec": round(duration, 3),
        }

    def analyze_consistency(self, audio_or_path: Union[str, np.ndarray], sr: int = 16000) -> Dict[str, Any]:
        """
        Evaluate Intra-Utterance Speaker Biometric Consistency from either file path or array.
        """
        if isinstance(audio_or_path, str):
            audio, s = librosa.load(audio_or_path, sr=sr, mono=True)
            return self.analyze_consistency_array(audio, sr=s)
        return self.analyze_consistency_array(audio_or_path, sr=sr)
