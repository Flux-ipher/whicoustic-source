"""
Generate and Evaluate 100 Partial Fakes Benchmark Suite

Addresses Phase 2 Sub-Problem B requirement:
"Build 100 partial fakes and locate the synthetic segments (F1 at 0.5-second resolution)"

This script:
1. Generates 100 distinct partial-fake audio clips with randomized splice configurations:
   - Variable splice durations (0.5s to 2.5s)
   - Variable positions: Prefix (start), Infix (middle), Suffix (end), and Multi-splice
   - Both Clean 16kHz and Telephone 8kHz channel conditions
2. Saves clips and full ground-truth frame-level manifest to `data/partial_fakes_100/`.
3. Runs `PartialFakeLocalizer` across all 100 clips at 0.5s resolution.
4. Computes aggregate Precision, Recall, Accuracy, and F1 Score.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import soundfile as sf

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.services.partial_fake_localizer import PartialFakeLocalizer
from app.services.telephone_channel import TelephoneChannelPreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("partial_fakes_100")


def generate_speech_wave(duration_s: float, sr: int = 16000, is_fake: bool = False, base_pitch: float = 130.0) -> np.ndarray:
    """Generate human-like or synthetic vocal tract waveform with natural formant variations."""
    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False, dtype=np.float32)
    f0 = base_pitch

    if not is_fake:
        # Human speech: pitch micro-jitter, vibrato, breathing noise, natural formant peaks
        jitter = 1.0 + 0.025 * np.sin(2 * np.pi * 5.5 * t)
        wave = (
            0.5 * np.sin(2 * np.pi * f0 * jitter * t)
            + 0.3 * np.sin(2 * np.pi * 2 * f0 * jitter * t)
            + 0.15 * np.sin(2 * np.pi * 3 * f0 * jitter * t)
            + 0.12 * np.sin(2 * np.pi * 750.0 * t)   # Formant F1
            + 0.09 * np.sin(2 * np.pi * 1250.0 * t)  # Formant F2
            + 0.04 * np.random.normal(0, 0.04, len(t)).astype(np.float32)
        )
    else:
        # Cloned TTS: rigid harmonic combs, zero jitter, buzzing overtones, high spectral flatness
        wave = (
            0.55 * np.sin(2 * np.pi * f0 * t)
            + 0.45 * np.sin(2 * np.pi * 2 * f0 * t)
            + 0.35 * np.sin(2 * np.pi * 3 * f0 * t)
            + 0.25 * np.sin(2 * np.pi * 4 * f0 * t)
            + 0.18 * np.sin(2 * np.pi * 5 * f0 * t)
            + 0.01 * np.random.normal(0, 0.01, len(t)).astype(np.float32)
        )

    # Normalize amplitude
    max_val = np.max(np.abs(wave))
    if max_val > 0:
        wave /= max_val
    return wave.astype(np.float32)


def generate_and_evaluate_100_fakes(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"

    logger.info("Generating 100 partial-fake benchmark clips in %s...", output_dir)
    np.random.seed(42)  # Deterministic benchmark generation

    sr = 16000
    localizer = PartialFakeLocalizer(sample_rate=sr)
    preprocessor = TelephoneChannelPreprocessor(target_sr=sr)

    manifest: List[Dict[str, Any]] = []
    clip_evaluations: List[Dict[str, Any]] = []

    total_tp = 0
    total_fp = 0
    total_tn = 0
    total_fn = 0
    correct_clip_verdicts = 0

    for i in range(1, 101):
        # Clip durations range from 3.0s to 5.0s (in steps of 0.5s)
        total_duration = float(np.random.choice([3.0, 3.5, 4.0, 4.5, 5.0]))
        num_windows = int(total_duration / 0.5)

        # Base human pitch (100Hz to 180Hz)
        human_pitch = float(np.random.uniform(110.0, 160.0))
        human_audio = generate_speech_wave(total_duration, sr, is_fake=False, base_pitch=human_pitch)

        # Splice configuration type
        # 1 = Infix (middle splice), 2 = Prefix (starts fake), 3 = Suffix (ends fake), 4 = Multi-splice
        splice_type = i % 4
        fake_spans: List[Tuple[float, float]] = []

        if splice_type == 0:  # Infix (middle splice)
            start_s = float(np.random.choice([0.5, 1.0, 1.5]))
            dur_s = float(np.random.choice([1.0, 1.5, 2.0]))
            end_s = min(start_s + dur_s, total_duration - 0.5)
            fake_spans.append((round(start_s, 2), round(end_s, 2)))

        elif splice_type == 1:  # Prefix (start splice)
            dur_s = float(np.random.choice([1.0, 1.5]))
            fake_spans.append((0.0, round(dur_s, 2)))

        elif splice_type == 2:  # Suffix (end splice)
            dur_s = float(np.random.choice([1.0, 1.5]))
            fake_spans.append((round(total_duration - dur_s, 2), round(total_duration, 2)))

        else:  # Multi-splice (two separate synthetic insertions)
            fake_spans.append((0.5, 1.0))
            if total_duration >= 4.0:
                fake_spans.append((2.5, 3.5))
            else:
                fake_spans.append((2.0, 2.5))

        # Splice fake segments into human audio
        synthetic_audio = human_audio.copy()
        for s_start, s_end in fake_spans:
            s_len = s_end - s_start
            fake_chunk = generate_speech_wave(s_len, sr, is_fake=True, base_pitch=human_pitch + 15.0)
            start_idx = int(s_start * sr)
            end_idx = int(s_end * sr)
            synthetic_audio[start_idx:end_idx] = fake_chunk[: end_idx - start_idx]

        # 30% of clips evaluated under telephone channel degradation (8kHz + G.711)
        is_telephony = (i % 3 == 0)
        eval_audio = synthetic_audio
        if is_telephony:
            eval_audio = preprocessor.simulate_telephony(synthetic_audio, sr, codec="g711_ulaw", snr_db=25.0)

        # Save clip
        filename = f"partial_fake_{i:03d}.wav"
        file_path = output_dir / filename
        sf.write(str(file_path), eval_audio, sr)

        # Run localization analysis
        res = localizer.analyze_audio(
            audio=eval_audio,
            sr=sr,
            ground_truth_spans=fake_spans,
            is_telephony=is_telephony,
        )

        metrics = res.get("metrics") or {}
        tp = metrics.get("tp_segments", 0)
        fp = metrics.get("fp_segments", 0)
        tn = metrics.get("tn_segments", 0)
        fn = metrics.get("fn_segments", 0)

        total_tp += tp
        total_fp += fp
        total_tn += tn
        total_fn += fn

        clip_verdict_correct = (res.get("clip_verdict") == "PARTIAL_FAKE")
        if clip_verdict_correct:
            correct_clip_verdicts += 1

        manifest_item = {
            "clip_id": i,
            "filename": filename,
            "total_duration_s": total_duration,
            "is_telephony": is_telephony,
            "ground_truth_fake_spans": fake_spans,
            "predicted_clip_verdict": res.get("clip_verdict"),
            "f1_score": metrics.get("f1_score", 0.0),
            "precision": metrics.get("precision", 0.0),
            "recall": metrics.get("recall", 0.0),
        }
        manifest.append(manifest_item)

    # Save manifest
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Compute overall dataset metrics
    precision = total_tp / max(total_tp + total_fp, 1)
    recall = total_tp / max(total_tp + total_fn, 1)
    f1 = (
        2.0 * (precision * recall) / max(precision + recall, 1e-10)
        if (precision + recall) > 0
        else 0.0
    )
    accuracy = (total_tp + total_tn) / max(total_tp + total_tn + total_fp + total_fn, 1)
    clip_accuracy = correct_clip_verdicts / 100.0

    summary = {
        "num_clips": 100,
        "total_evaluated_0_5s_frames": total_tp + total_fp + total_tn + total_fn,
        "true_positives": total_tp,
        "false_positives": total_fp,
        "true_negatives": total_tn,
        "false_negatives": total_fn,
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "frame_accuracy": round(float(accuracy), 4),
        "clip_level_verdict_accuracy": round(float(clip_accuracy), 4),
        "manifest_path": str(manifest_path),
    }

    # Print Report
    print("\n" + "=" * 78)
    print("      100 PARTIAL FAKES BENCHMARK REPORT (0.5s RESOLUTION)")
    print("=" * 78)
    print(f"Total Clips Generated & Tested:      100")
    print(f"Total 0.5s Frames Evaluated:         {summary['total_evaluated_0_5s_frames']}")
    print(f"Telephony-Degraded Clips (8kHz/G711): 33 / 100")
    print(f"Clean Studio Clips (16kHz):          67 / 100")
    print("-" * 78)
    print(f"True Positives  (Fake correctly caught):  {total_tp}")
    print(f"True Negatives  (Human preserved):       {total_tn}")
    print(f"False Positives (Human flagged as fake): {total_fp}")
    print(f"False Negatives (Fake missed):           {total_fn}")
    print("-" * 78)
    print(f"Precision:                           {summary['precision'] * 100:.2f}%")
    print(f"Recall:                              {summary['recall'] * 100:.2f}%")
    print(f"Segment-Level F1 Score:              {summary['f1_score'] * 100:.2f}% (F1 = {summary['f1_score']})")
    print(f"Frame-Level Accuracy:                {summary['frame_accuracy'] * 100:.2f}%")
    print(f"Clip-Level 'PARTIAL_FAKE' Detection: {summary['clip_level_verdict_accuracy'] * 100:.2f}%")
    print("=" * 78 + "\n")

    return summary


if __name__ == "__main__":
    target_dir = backend_root / "data" / "partial_fakes_100"
    generate_and_evaluate_100_fakes(target_dir)
