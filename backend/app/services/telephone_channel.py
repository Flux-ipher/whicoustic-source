"""
TelephoneChannelPreprocessor — Phase 2 Module 1: Telephone Channel Robustness & Preprocessing

Handles real phone call audio (8 kHz, codec-compressed, noisy):
1. Bandwidth detection: identifies 8kHz / telephone-bandlimited audio via spectral analysis.
2. Resampling & normalization: standardizes audio to 16kHz for pipeline compatibility.
3. Telephony noise filtering: applies light spectral subtraction / Wiener filtering.
4. Channel simulation (for evaluation/benchmarking): simulates G.711 (u-law/a-law), G.722,
   additive line noise, and bandpass filtering (300-3400 Hz).
5. Dynamic weight reallocation: suppresses Layer 6 (19kHz watermark) and high-frequency
   biases when phone audio is detected.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import numpy as np
from scipy import signal

logger = logging.getLogger(__name__)


class TelephoneChannelPreprocessor:
    """
    Preprocessor for telephony audio streams and static files.
    """

    TARGET_SR: int = 16000
    TELEPHONY_CUTOFF_HZ: float = 3800.0  # Nyquist for 8kHz is 4000Hz; cutoff near 3800Hz
    MIN_SPEECH_SAMPLES: int = 320

    def __init__(self, target_sr: int = 16000) -> None:
        self.target_sr = target_sr

    # ------------------------------------------------------------------
    # Bandwidth & Telephony Detection
    # ------------------------------------------------------------------

    def detect_bandwidth(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """
        Analyze whether an audio segment has been bandlimited by a telephony channel.

        Returns:
            dict containing:
              - is_telephony (bool): True if audio exhibits 8kHz / telephone bandlimiting
              - effective_bandwidth_hz (float): Estimated upper cutoff frequency
              - hf_energy_ratio (float): Ratio of energy > 3800Hz to total energy
              - detected_sr (int): Reported input sample rate
        """
        if len(audio) < self.MIN_SPEECH_SAMPLES:
            return {
                "is_telephony": (sr <= 8000),
                "effective_bandwidth_hz": min(float(sr) / 2.0, 4000.0) if sr <= 8000 else float(sr) / 2.0,
                "hf_energy_ratio": 0.0 if sr <= 8000 else 1.0,
                "detected_sr": sr,
            }

        # If sample rate is explicitly <= 8000, it's definitely telephony bandwidth
        if sr <= 8000:
            return {
                "is_telephony": True,
                "effective_bandwidth_hz": min(float(sr) / 2.0, 4000.0),
                "hf_energy_ratio": 0.0,
                "detected_sr": sr,
            }

        # For >= 16kHz audio, check if content above 3800Hz has zero or near-zero energy
        # (which happens when 8kHz audio was upsampled to 16kHz before reaching us)
        try:
            fft_mag = np.abs(np.fft.rfft(audio))
            freqs = np.fft.rfftfreq(len(audio), d=1.0 / sr)

            total_energy = float(np.sum(fft_mag ** 2)) + 1e-10
            hf_mask = freqs >= self.TELEPHONY_CUTOFF_HZ
            hf_energy = float(np.sum(fft_mag[hf_mask] ** 2))
            hf_ratio = hf_energy / total_energy

            # Cumulative energy for rolloff estimation (95th percentile)
            cum_energy = np.cumsum(fft_mag ** 2)
            rolloff_idx = np.searchsorted(cum_energy, 0.95 * total_energy)
            rolloff_hz = float(freqs[min(rolloff_idx, len(freqs) - 1)])

            # Real telephony (8kHz sample rate or sharp 3.4kHz bandpass) has virtually zero energy > 3800Hz
            is_telephony = (hf_ratio < 0.005 and rolloff_hz < 3600.0) or (sr <= 8000)

            return {
                "is_telephony": bool(is_telephony),
                "effective_bandwidth_hz": round(rolloff_hz, 1),
                "hf_energy_ratio": round(hf_ratio, 5),
                "detected_sr": sr,
            }
        except Exception as exc:
            logger.warning("Failed to estimate bandwidth: %s", exc)
            return {
                "is_telephony": (sr <= 8000),
                "effective_bandwidth_hz": float(sr) / 2.0,
                "hf_energy_ratio": 0.0 if sr <= 8000 else 0.5,
                "detected_sr": sr,
            }

    # ------------------------------------------------------------------
    # Preprocessing & Normalization
    # ------------------------------------------------------------------

    def preprocess(
        self, audio: np.ndarray, sr: int, denoise: bool = True
    ) -> Tuple[np.ndarray, int, Dict[str, Any]]:
        """
        Normalize audio for pipeline consumption:
        1. Converts int16 to float32 [-1.0, 1.0] if necessary.
        2. Detects telephony bandlimiting.
        3. Resamples to target_sr (16kHz) if needed.
        4. Applies telephony Wiener/spectral denoise if enabled.

        Returns:
            (processed_audio_f32, output_sr, metadata_dict)
        """
        # Ensure float32 in [-1.0, 1.0]
        if audio.dtype == np.int16:
            audio_f32 = audio.astype(np.float32) / 32768.0
        elif audio.dtype in (np.float32, np.float64):
            audio_f32 = audio.astype(np.float32)
            max_val = np.max(np.abs(audio_f32))
            if max_val > 1.0:
                audio_f32 = audio_f32 / max_val
        else:
            audio_f32 = audio.astype(np.float32)

        # Detect bandwidth characteristics
        meta = self.detect_bandwidth(audio_f32, sr)

        # Resample to 16kHz if needed
        out_sr = sr
        if sr != self.target_sr:
            audio_f32 = self.resample_audio(audio_f32, orig_sr=sr, target_sr=self.target_sr)
            out_sr = self.target_sr

        # Noise mitigation (Wiener-style filter for telephony hiss)
        if denoise and len(audio_f32) >= 512:
            audio_f32 = self._wiener_denoise(audio_f32)

        return audio_f32, out_sr, meta

    def resample_audio(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Polyphase / Fourier resampling without requiring external resampler binaries.
        """
        if orig_sr == target_sr:
            return audio
        try:
            # Greatest common divisor for rational resampling
            import math
            gcd = math.gcd(orig_sr, target_sr)
            up = target_sr // gcd
            down = orig_sr // gcd
            return signal.resample_poly(audio, up, down).astype(np.float32)
        except Exception:
            # Fallback to FFT resampling
            target_len = int(round(len(audio) * float(target_sr) / float(orig_sr)))
            return signal.resample(audio, target_len).astype(np.float32)

    def _wiener_denoise(self, audio: np.ndarray, noise_floor_ratio: float = 0.05) -> np.ndarray:
        """
        Fast spectral subtraction / Wiener filter for background phone hiss.
        Preserves phase and applies gain = max(0, 1 - (Noise_P / Signal_P)).
        """
        try:
            # Use STFT
            n_fft = min(512, len(audio))
            hop = n_fft // 2
            window = np.hanning(n_fft)
            
            # Frame the audio
            n_frames = 1 + (len(audio) - n_fft) // hop
            if n_frames < 2:
                return audio

            frames = np.lib.stride_tricks.sliding_window_view(audio[: (n_frames - 1) * hop + n_fft], n_fft)[::hop]
            windowed = frames * window
            stft = np.fft.rfft(windowed, axis=-1)
            mag = np.abs(stft)
            phase = np.angle(stft)

            # Estimate noise profile from 10th percentile lowest-energy frames
            frame_powers = np.mean(mag ** 2, axis=1)
            lowest_k = max(1, int(len(frame_powers) * 0.15))
            noise_idx = np.argsort(frame_powers)[:lowest_k]
            noise_psd = np.mean(mag[noise_idx] ** 2, axis=0, keepdims=True)

            # Wiener gain with protective spectral floor to preserve voice harmonics
            signal_psd = mag ** 2
            wiener_gain = np.clip(1.0 - (noise_psd / (signal_psd + 1e-10)), 0.35, 1.0)
            clean_mag = mag * wiener_gain

            # Reconstruct
            clean_stft = clean_mag * np.exp(1j * phase)
            reconstructed_frames = np.fft.irfft(clean_stft, axis=-1) * window

            # Overlap-add
            output = np.zeros(len(audio), dtype=np.float32)
            window_norm = np.zeros(len(audio), dtype=np.float32)

            for i in range(len(reconstructed_frames)):
                start = i * hop
                end = start + n_fft
                output[start:end] += reconstructed_frames[i]
                window_norm[start:end] += window ** 2

            # Normalize overlap
            nonzero = window_norm > 1e-6
            output[nonzero] /= window_norm[nonzero]
            return output
        except Exception as exc:
            logger.debug("Wiener denoise skipped due to: %s", exc)
            return audio

    # ------------------------------------------------------------------
    # Telephony Dynamic Weight Reallocation
    # ------------------------------------------------------------------

    @staticmethod
    def adjust_layer_weights(weights: Dict[str, Any], is_telephony: bool) -> Dict[str, Any]:
        """
        In telephony mode, Layer 6 (19kHz watermark) is destroyed by 8kHz resampling.
        Mark L6 as disabled and redistribute its weight across the remaining active layers.
        """
        adjusted = {k: dict(v) for k, v in weights.items()}

        if is_telephony and "l6" in adjusted:
            # Disable Layer 6
            l6_weight = adjusted["l6"].get("weight", 0.20)
            adjusted["l6"]["weight"] = 0.0
            adjusted["l6"]["status"] = "disabled_telephony"
            adjusted["l6"]["notes"] = "19kHz watermark inaudible on 8kHz telephone channel"

            # Redistribute weight among active layers
            active_keys = [k for k in adjusted if k != "l6" and adjusted[k].get("weight", 0) > 0]
            if active_keys and l6_weight > 0:
                bonus_per_layer = l6_weight / len(active_keys)
                for k in active_keys:
                    adjusted[k]["weight"] = round(adjusted[k]["weight"] + bonus_per_layer, 4)

        return adjusted

    # ------------------------------------------------------------------
    # Codec & Channel Simulation (For Evaluation & Robustness Benchmarks)
    # ------------------------------------------------------------------

    @staticmethod
    def simulate_telephony(
        audio: np.ndarray,
        sr: int,
        codec: str = "g711_ulaw",
        snr_db: Optional[float] = 20.0,
        bandpass: bool = True,
    ) -> np.ndarray:
        """
        Simulate telephone channel degradation on clean audio for robustness testing:
        - Downsample to 8kHz
        - Apply 300-3400 Hz telephone bandpass filter
        - Apply G.711 mu-law or a-law companding / quantisation
        - Add AWGN / channel line noise at target SNR
        - Upsample back to 16kHz for pipeline ingestion
        """
        # 1. Resample to 8kHz
        if sr != 8000:
            target_len = int(round(len(audio) * 8000.0 / float(sr)))
            audio_8k = signal.resample(audio, target_len).astype(np.float32)
        else:
            audio_8k = audio.astype(np.float32).copy()

        # 2. Bandpass 300 - 3400 Hz (Standard PSTN speech filter)
        if bandpass and len(audio_8k) > 64:
            try:
                sos = signal.butter(4, [300.0, 3400.0], btype="bandpass", fs=8000, output="sos")
                audio_8k = signal.sosfilt(sos, audio_8k).astype(np.float32)
            except Exception:
                pass

        # 3. Codec quantization
        if codec == "g711_ulaw":
            audio_8k = TelephoneChannelPreprocessor._apply_ulaw(audio_8k)
        elif codec == "g711_alaw":
            audio_8k = TelephoneChannelPreprocessor._apply_alaw(audio_8k)
        elif codec == "g722":
            audio_8k = TelephoneChannelPreprocessor._apply_g722_quant(audio_8k)

        # 4. Add channel noise (SNR in dB)
        if snr_db is not None:
            sig_power = float(np.mean(audio_8k ** 2)) + 1e-10
            noise_power = sig_power / (10.0 ** (snr_db / 10.0))
            noise = np.random.normal(0, np.sqrt(noise_power), len(audio_8k)).astype(np.float32)
            audio_8k = audio_8k + noise

        # 5. Return at 16kHz for detector processing
        out_len = int(round(len(audio_8k) * 16000.0 / 8000.0))
        return signal.resample(audio_8k, out_len).astype(np.float32)

    @staticmethod
    def _apply_ulaw(x: np.ndarray, mu: float = 255.0) -> np.ndarray:
        """Standard G.711 mu-law 8-bit companding and expansion."""
        x = np.clip(x, -1.0, 1.0)
        # Compand
        companded = np.sign(x) * np.log1p(mu * np.abs(x)) / np.log1p(mu)
        # Quantize to 8-bit (256 discrete levels in [-1, 1])
        quantized = np.round(companded * 128.0) / 128.0
        # Expand
        expanded = np.sign(quantized) * (1.0 / mu) * ((1.0 + mu) ** np.abs(quantized) - 1.0)
        return expanded.astype(np.float32)

    @staticmethod
    def _apply_alaw(x: np.ndarray, a: float = 87.6) -> np.ndarray:
        """Standard G.711 A-law 8-bit companding and expansion."""
        x = np.clip(x, -1.0, 1.0)
        abs_x = np.abs(x)
        companded = np.zeros_like(x)

        idx1 = abs_x < (1.0 / a)
        idx2 = ~idx1

        companded[idx1] = (a * abs_x[idx1]) / (1.0 + np.log(a))
        companded[idx2] = (1.0 + np.log(a * abs_x[idx2])) / (1.0 + np.log(a))
        companded = np.sign(x) * companded

        # 8-bit quantization
        quantized = np.round(companded * 128.0) / 128.0
        abs_q = np.abs(quantized)

        expanded = np.zeros_like(quantized)
        e_idx1 = abs_q < (1.0 / (1.0 + np.log(a)))
        e_idx2 = ~e_idx1

        expanded[e_idx1] = abs_q[e_idx1] * (1.0 + np.log(a)) / a
        expanded[e_idx2] = np.exp(abs_q[e_idx2] * (1.0 + np.log(a)) - 1.0) / a
        return (np.sign(quantized) * expanded).astype(np.float32)

    @staticmethod
    def _apply_g722_quant(x: np.ndarray) -> np.ndarray:
        """Approximation of G.722 sub-band ADPCM quantization (14-bit equivalent)."""
        x = np.clip(x, -1.0, 1.0)
        levels = 16384.0  # 14-bit
        return (np.round(x * levels) / levels).astype(np.float32)
