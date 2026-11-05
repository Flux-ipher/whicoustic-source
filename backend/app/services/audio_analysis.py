"""
Audio analysis utilities for graphs and metrics.
Returns compact arrays for plotting (mel-spectrogram, MFCC, spectral stats).
"""
from __future__ import annotations

import numpy as np
import librosa
from typing import Dict, Any


class AudioAnalysisService:
    def analyze(self, path: str) -> Dict[str, Any]:
        y, sr = librosa.load(path, sr=22050, mono=True)
        # Mel-spectrogram
        mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=64, fmax=sr // 2)
        mel_db = librosa.power_to_db(mel, ref=np.max)
        # MFCC
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
        # Spectral features
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        # Downsample along time for payload size
        def ds(arr, factor=4):
            if arr.ndim == 2:
                return arr[:, ::factor]
            return arr[::factor]
        return {
            "sr": sr,
            "mel_db": ds(mel_db).astype(float).tolist(),
            "mfcc": ds(mfcc).astype(float).tolist(),
            "centroid": ds(centroid).astype(float).tolist(),
            "bandwidth": ds(bandwidth).astype(float).tolist(),
            "rolloff": ds(rolloff).astype(float).tolist(),
            "zcr": ds(zcr).astype(float).tolist(),
        }