"""
PartialFakeLocalizer — Phase 2 Module 2: Segment-Level Deepfake Localization

Addresses Phase 2 Sub-Problem B:
1. Runs sliding-window analysis at 0.5-second resolution.
2. Identifies exact boundaries of synthetic spliced segments in partial fakes.
3. Computes Precision, Recall, and F1 score against ground-truth labels at 0.5s resolution.
4. Generates continuous synthetic spans and overall classification:
   - "CLEAN_HUMAN": all segments authentic
   - "FULL_FAKE": all segments synthetic
   - "PARTIAL_FAKE": mixed human and synthetic segments
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .antispoof import AntiSpoofDetector
from .prosody_service import ProsodyService
from .paralinguistic_service import ParalinguisticService
from .risk_scoring import combine_layer_results
from .telephone_channel import TelephoneChannelPreprocessor

logger = logging.getLogger(__name__)


class PartialFakeLocalizer:
    """
    Localizes synthetic audio segments at 0.5s resolution.
    """

    RESOLUTION_S: float = 0.5  # 500ms segment resolution
    TARGET_SR: int = 16000

    def __init__(self, sample_rate: int = 16000, threshold: float = 0.40) -> None:
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.segment_samples = int(self.RESOLUTION_S * sample_rate)

        # Fast acoustic layer detectors
        self._antispoof = AntiSpoofDetector()
        self._prosody = ProsodyService()
        self._paralinguistic = ParalinguisticService()
        self._preprocessor = TelephoneChannelPreprocessor(target_sr=sample_rate)

    def analyze_audio(
        self,
        audio: np.ndarray,
        sr: int,
        ground_truth_spans: Optional[List[Tuple[float, float]]] = None,
        is_telephony: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Analyze audio and produce frame-by-frame 0.5s segment labels.

        Args:
            audio: Input audio array (float32 or int16)
            sr: Sample rate
            ground_truth_spans: Optional list of (start_s, end_s) indicating known fake segments
            is_telephony: Optional override for telephone mode

        Returns:
            Dict containing segment-by-segment predictions, merged spans,
            overall verdict, and optional F1 metrics.
        """
        # Preprocess and resample if needed
        audio_f32, effective_sr, tele_meta = self._preprocessor.preprocess(audio, sr)
        if is_telephony is None:
            is_telephony = tele_meta.get("is_telephony", False)

        total_samples = len(audio_f32)
        total_duration_s = round(total_samples / effective_sr, 2)

        if total_samples < self.segment_samples:
            # Clip is shorter than one 0.5s window
            score = self._score_window(audio_f32, effective_sr, is_telephony)
            label = "REAL" if score >= self.threshold else "FAKE"
            return {
                "total_duration_s": total_duration_s,
                "resolution_s": self.RESOLUTION_S,
                "is_telephony": is_telephony,
                "clip_verdict": "CLEAN_HUMAN" if label == "REAL" else "FULL_FAKE",
                "fake_segments_s": 0.0 if label == "REAL" else total_duration_s,
                "real_segments_s": total_duration_s if label == "REAL" else 0.0,
                "segments": [{"start_s": 0.0, "end_s": total_duration_s, "score": score, "label": label}],
                "spans": [{"start_s": 0.0, "end_s": total_duration_s, "label": label, "duration_s": total_duration_s}],
                "metrics": None,
            }

        # Slide window with 0.5s step
        segments: List[Dict[str, Any]] = []
        hop_samples = self.segment_samples
        num_windows = int(np.ceil(total_samples / hop_samples))

        for idx in range(num_windows):
            start_sample = idx * hop_samples
            end_sample = min(start_sample + hop_samples, total_samples)
            window = audio_f32[start_sample:end_sample]

            # Zero-pad if final partial frame
            if len(window) < hop_samples:
                window = np.pad(window, (0, hop_samples - len(window)))

            # Check for silent pauses / breath intake in this 0.5s window
            global_rms = float(np.sqrt(np.mean(audio_f32 ** 2))) + 1e-6
            window_rms = float(np.sqrt(np.mean(window ** 2)))
            is_silence = (window_rms < 0.004) or (window_rms < global_rms * 0.08)

            if is_silence:
                score = 0.60  # Natural pause between words
                label = "REAL"
            else:
                score = self._score_window(window, effective_sr, is_telephony)
                label = "REAL" if score >= self.threshold else "FAKE"

            start_s = round(start_sample / effective_sr, 2)
            end_s = round(end_sample / effective_sr, 2)

            segments.append({
                "segment_index": idx,
                "start_s": start_s,
                "end_s": end_s,
                "score": score,
                "label": label,
            })

        # Merge adjacent same-label segments into contiguous spans
        spans = self._merge_into_spans(segments)

        # Compute durations
        fake_duration_s = round(
            sum(s["end_s"] - s["start_s"] for s in segments if s["label"] == "FAKE"), 2
        )
        real_duration_s = round(
            sum(s["end_s"] - s["start_s"] for s in segments if s["label"] == "REAL"), 2
        )

        # Classify overall clip
        fake_ratio = fake_duration_s / max(total_duration_s, 0.001)
        max_consecutive_fake_s = max([s["duration_s"] for s in spans if s["label"] == "FAKE"], default=0.0)

        # Require at least an 0.8s cluster or 8% of speech to declare a spliced partial fake
        if fake_duration_s == 0 or (max_consecutive_fake_s < 0.8 and fake_ratio < 0.08):
            clip_verdict = "CLEAN_HUMAN"
        elif real_duration_s == 0 or fake_ratio >= 0.85:
            clip_verdict = "FULL_FAKE"
        else:
            clip_verdict = "PARTIAL_FAKE"

        # Calculate F1 score if ground truth is supplied
        metrics = None
        if ground_truth_spans is not None:
            metrics = self._evaluate_f1(segments, ground_truth_spans)

        return {
            "total_duration_s": total_duration_s,
            "resolution_s": self.RESOLUTION_S,
            "is_telephony": is_telephony,
            "clip_verdict": clip_verdict,
            "fake_segments_s": fake_duration_s,
            "real_segments_s": real_duration_s,
            "fake_ratio": round(fake_ratio, 3),
            "segments": segments,
            "spans": spans,
            "metrics": metrics,
        }

    def _score_window(self, window: np.ndarray, sr: int, is_telephony: bool) -> float:
        """Score an individual 0.5s window using fast-path layers."""
        results: Dict[str, Any] = {}
        weights: Dict[str, Any] = {}

        # Layer 1: Anti-spoof
        try:
            l1 = self._antispoof.detect_array(window, sr)
            auth_l1 = max(0.0, 1.0 - l1.get("spoof_score", 0.5))
            results["layer1_antispoof"] = l1
            weights["l1"] = {"score": auth_l1, "weight": 0.40}
        except Exception:
            weights["l1"] = {"score": 0.5, "weight": 0.40}

        # Layer 3: Prosody
        try:
            l3 = self._prosody.analyse_array(window, sr)
            auth_l3 = l3.get("authenticity_score", 0.5)
            results["layer3_prosody"] = l3
            weights["l3"] = {"score": auth_l3, "weight": 0.35}
        except Exception:
            weights["l3"] = {"score": 0.5, "weight": 0.35}

        # Layer 4: Paralinguistic
        try:
            l4 = self._paralinguistic.analyse_array(window, sr)
            auth_l4 = l4.get("authenticity_score", 0.5)
            results["layer4_paralinguistic"] = l4
            weights["l4"] = {"score": auth_l4, "weight": 0.25}
        except Exception:
            weights["l4"] = {"score": 0.5, "weight": 0.25}

        if is_telephony:
            weights = self._preprocessor.adjust_layer_weights(weights, is_telephony=True)

        verdict = combine_layer_results(results, weights)
        return round(float(verdict.get("overall_authenticity_score", 0.5)), 4)

    def _merge_into_spans(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge adjacent segments with the same label into continuous spans."""
        if not segments:
            return []

        spans: List[Dict[str, Any]] = []
        curr_span = {
            "start_s": segments[0]["start_s"],
            "end_s": segments[0]["end_s"],
            "label": segments[0]["label"],
            "avg_score": segments[0]["score"],
            "count": 1,
        }

        for seg in segments[1:]:
            if seg["label"] == curr_span["label"]:
                curr_span["end_s"] = seg["end_s"]
                curr_span["avg_score"] += seg["score"]
                curr_span["count"] += 1
            else:
                curr_span["avg_score"] = round(curr_span["avg_score"] / curr_span["count"], 4)
                curr_span["duration_s"] = round(curr_span["end_s"] - curr_span["start_s"], 2)
                spans.append({
                    "start_s": curr_span["start_s"],
                    "end_s": curr_span["end_s"],
                    "duration_s": curr_span["duration_s"],
                    "label": curr_span["label"],
                    "confidence": curr_span["avg_score"],
                })
                curr_span = {
                    "start_s": seg["start_s"],
                    "end_s": seg["end_s"],
                    "label": seg["label"],
                    "avg_score": seg["score"],
                    "count": 1,
                }

        curr_span["avg_score"] = round(curr_span["avg_score"] / curr_span["count"], 4)
        curr_span["duration_s"] = round(curr_span["end_s"] - curr_span["start_s"], 2)
        spans.append({
            "start_s": curr_span["start_s"],
            "end_s": curr_span["end_s"],
            "duration_s": curr_span["duration_s"],
            "label": curr_span["label"],
            "confidence": curr_span["avg_score"],
        })
        return spans

    def _evaluate_f1(
        self,
        segments: List[Dict[str, Any]],
        ground_truth_spans: List[Tuple[float, float]],
    ) -> Dict[str, Any]:
        """
        Evaluate frame-level classification performance against ground truth fake spans.
        Resolution: 0.5-second windows.
        """
        tp = 0  # Predicted FAKE, Actually FAKE
        fp = 0  # Predicted FAKE, Actually REAL
        tn = 0  # Predicted REAL, Actually REAL
        fn = 0  # Predicted REAL, Actually FAKE

        for seg in segments:
            midpoint = (seg["start_s"] + seg["end_s"]) / 2.0
            is_truth_fake = any(
                start <= midpoint <= end for start, end in ground_truth_spans
            )
            pred_fake = (seg["label"] == "FAKE")

            if pred_fake and is_truth_fake:
                tp += 1
            elif pred_fake and not is_truth_fake:
                fp += 1
            elif not pred_fake and not is_truth_fake:
                tn += 1
            else:
                fn += 1

        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = (
            2.0 * (precision * recall) / max(precision + recall, 1e-10)
            if (precision + recall) > 0
            else 0.0
        )
        accuracy = (tp + tn) / max(tp + tn + fp + fn, 1)

        return {
            "f1_score": round(float(f1), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "accuracy": round(float(accuracy), 4),
            "tp_segments": tp,
            "fp_segments": fp,
            "tn_segments": tn,
            "fn_segments": fn,
            "total_evaluated_segments": len(segments),
        }

    # ------------------------------------------------------------------
    # Partial Fake Audio Construction Utility
    # ------------------------------------------------------------------

    @staticmethod
    def construct_partial_fake(
        real_audio: np.ndarray,
        fake_audio: np.ndarray,
        splice_start_s: float,
        splice_duration_s: float,
        sr: int = 16000,
        crossfade_ms: float = 20.0,
    ) -> Tuple[np.ndarray, List[Tuple[float, float]]]:
        """
        Utility for generating benchmark partial-fake clips with ground truth intervals.
        """
        start_samp = int(splice_start_s * sr)
        splice_len = int(splice_duration_s * sr)
        end_samp = start_samp + splice_len

        # Ensure fake_audio is long enough
        if len(fake_audio) < splice_len:
            fake_segment = np.tile(fake_audio, int(np.ceil(splice_len / max(len(fake_audio), 1))))[:splice_len]
        else:
            fake_segment = fake_audio[:splice_len]

        output = real_audio.copy()
        if end_samp > len(output):
            output = np.pad(output, (0, end_samp - len(output)))

        # Crossfade to prevent harsh click artifacts at splice boundaries
        fade_samples = int((crossfade_ms / 1000.0) * sr)
        if fade_samples > 0 and fade_samples < splice_len:
            fade_in = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
            fade_out = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)

            fake_segment[:fade_samples] *= fade_in
            fake_segment[-fade_samples:] *= fade_out

        output[start_samp:end_samp] = fake_segment
        actual_end_s = round(end_samp / sr, 2)
        ground_truth = [(round(splice_start_s, 2), actual_end_s)]

        return output, ground_truth
