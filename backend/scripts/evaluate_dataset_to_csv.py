"""
Whicoustic Dataset Evaluation & Batch Verification Tool
Scans an audio dataset directory, runs all 6 Deepfake Defense Layers, Telephony
Detection, and Partial-Fake Localization, and exports the complete results to a CSV file.

Features:
- Configurable Batch Processing (--batch-size, default: 50)
- Real-time Accuracy tracking for Human-voice or Deepfake benchmarks
- Per-batch performance reports with cumulative accuracy and false-alarm rates
- Automatic Resume (--resume) to skip already processed files
- JSON status & progress tracking

Usage:
    python backend/scripts/evaluate_dataset_to_csv.py --input-dir /path/to/dataset --output-csv results.csv --batch-size 50 --ground-truth human
"""

import os
import sys
import time
import csv
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor
import numpy as np

# Ensure backend modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["ENVIRONMENT"] = "development"
os.environ["MOCK_AUTH_ENABLED"] = "true"

import logging
logging.getLogger("app.services.open_source_voice_detector").setLevel(logging.CRITICAL)
logging.getLogger("app.services.antispoof").setLevel(logging.CRITICAL)
logging.getLogger("librosa").setLevel(logging.CRITICAL)

from app.services.antispoof import AntiSpoofDetector
from app.services.prosody_service import ProsodyService
from app.services.paralinguistic_service import ParalinguisticService
from app.services.speaker_verification import SpeakerVerifier
from app.services.semantic_service import SemanticService
from app.core.watermark import WatermarkDecoder
from app.services.telephone_channel import TelephoneChannelPreprocessor
from app.services.partial_fake_localizer import PartialFakeLocalizer

# Supported audio extensions
AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".wma"}

CSV_COLUMNS = [
    "file_name",
    "file_path",
    "file_format",
    "duration_sec",
    "sample_rate",
    "channels",
    "ground_truth",
    "overall_authenticity_score",
    "verdict",
    "is_synthetic",
    "is_correct",
    "layer1_antispoof_score",
    "layer1_spoof_probability",
    "layer1_engine",
    "layer2_speaker_similarity",
    "layer3_prosody_score",
    "layer3_pitch_cv",
    "layer3_voiced_ratio",
    "layer4_paralinguistic_score",
    "layer4_energy_cv",
    "layer5_semantic_score",
    "speech_rate_wpm",
    "transcription",
    "layer6_watermark_found",
    "layer6_watermark_confidence",
    "layer6_watermark_id",
    "is_telephony",
    "effective_bandwidth_hz",
    "hf_energy_ratio",
    "partial_fake_verdict",
    "spliced_segments",
    "processing_time_ms",
    "error"
]


def get_audio_info(file_path: str):
    """Retrieve audio metadata using soundfile or librosa."""
    import soundfile as sf
    try:
        info = sf.info(file_path)
        return float(info.duration), int(info.samplerate), int(info.channels), str(info.format)
    except Exception:
        import librosa
        y, sr = librosa.load(file_path, sr=None)
        duration = float(len(y) / sr)
        channels = 1 if y.ndim == 1 else y.shape[0]
        return duration, int(sr), channels, Path(file_path).suffix.replace(".", "").upper()


def analyze_single_audio(
    file_path: str,
    antispoof_detector: AntiSpoofDetector,
    prosody_service: ProsodyService,
    paralinguistic_service: ParalinguisticService,
    watermark_decoder: WatermarkDecoder,
    telephony_preproc: TelephoneChannelPreprocessor,
    localizer: PartialFakeLocalizer,
    ground_truth: str = "human",
    threshold: float = 0.45,
    reference_speaker_path: Optional[str] = None,
    speaker_verifier: Optional[SpeakerVerifier] = None,
    semantic_service: Optional[SemanticService] = None
) -> Dict[str, Any]:
    """Run comprehensive analysis on a single audio file."""
    start_t = time.time()
    result: Dict[str, Any] = {
        "file_name": os.path.basename(file_path),
        "file_path": str(Path(file_path).resolve()),
        "file_format": Path(file_path).suffix.lower(),
        "ground_truth": ground_truth,
        "error": None
    }

    try:
        import librosa
        audio_native, sr_native = librosa.load(file_path, sr=None)
        duration = float(len(audio_native) / sr_native)
        channels = 1 if audio_native.ndim == 1 else audio_native.shape[0]
        sample_rate = int(sr_native)

        result["duration_sec"] = round(duration, 3)
        result["sample_rate"] = sample_rate
        result["channels"] = channels

        # 1. Telephony & Bandwidth Detection
        tele_meta = telephony_preproc.detect_bandwidth(audio_native, sr_native)
        is_telephony = tele_meta.get("is_telephony", False)
        result["is_telephony"] = is_telephony
        result["effective_bandwidth_hz"] = tele_meta.get("effective_bandwidth_hz", 0.0)
        result["hf_energy_ratio"] = tele_meta.get("hf_energy_ratio", 0.0)

        # 2. Standardize audio to 16kHz for deepfake defense models
        if sr_native != 16000:
            audio_16k = librosa.resample(audio_native, orig_sr=sr_native, target_sr=16000)
        else:
            audio_16k = audio_native

        # 3. Layer 1: Acoustic Anti-Spoof
        spoof_res = antispoof_detector.detect_array(audio_16k, sr=16000)
        l1_spoof_prob = float(spoof_res.get("spoof_score", 0.5))
        l1_auth_score = max(0.0, min(1.0, 1.0 - l1_spoof_prob))
        result["layer1_antispoof_score"] = round(l1_auth_score, 4)
        result["layer1_spoof_probability"] = round(l1_spoof_prob, 4)
        result["layer1_engine"] = spoof_res.get("engine", "heuristic")

        # 4. Layer 2: Speaker Verification (Identity Consistency & Biometric Stability)
        l2_auth_score = None
        if speaker_verifier:
            try:
                if reference_speaker_path and os.path.exists(reference_speaker_path):
                    spk_res = speaker_verifier.verify(ref_path=reference_speaker_path, qry_path=file_path)
                else:
                    spk_res = speaker_verifier.analyze_consistency_array(audio_16k, sr=16000)
                l2_auth_score = float(spk_res.get("consistency_score", spk_res.get("similarity_score", 0.85)))
                result["layer2_speaker_similarity"] = round(l2_auth_score, 4)
            except Exception:
                result["layer2_speaker_similarity"] = None
        else:
            result["layer2_speaker_similarity"] = None

        # 5. Layer 3: Prosody Naturalness
        prosody_res = prosody_service.analyse_array(audio_16k, sr=16000)
        l3_auth_score = float(prosody_res.get("authenticity_score", 0.5))
        result["layer3_prosody_score"] = round(l3_auth_score, 4)
        result["layer3_pitch_cv"] = round(prosody_res.get("pitch_stability_cv", 0.0) or 0.0, 4)
        result["layer3_voiced_ratio"] = round(prosody_res.get("voiced_frame_ratio", 0.0) or 0.0, 4)

        # 6. Layer 4: Paralinguistics & Spectral Dynamics
        para_res = paralinguistic_service.analyse_array(audio_16k, sr=16000)
        l4_auth_score = float(para_res.get("authenticity_score", 0.5))
        result["layer4_paralinguistic_score"] = round(l4_auth_score, 4)
        result["layer4_energy_cv"] = round(para_res.get("arousal_variance", 0.0) or 0.0, 4)

        # 7. Layer 5: Semantic Consistency (Speech Rate, Pause Dynamics, Transcription)
        l5_auth_score = None
        transcription_text = ""
        speech_rate = None
        if semantic_service:
            try:
                sem_res = semantic_service.analyse_array(audio_16k, sr=16000)
                l5_auth_score = float(sem_res.get("authenticity_score", 0.50))
                transcription_text = sem_res.get("transcription") or ""
                speech_rate = sem_res.get("speech_rate_wpm")
                result["layer5_semantic_score"] = round(l5_auth_score, 4)
                result["transcription"] = transcription_text
                result["speech_rate_wpm"] = speech_rate
            except Exception:
                result["layer5_semantic_score"] = 0.50
                result["transcription"] = ""
                result["speech_rate_wpm"] = None
        else:
            result["layer5_semantic_score"] = 0.50
            result["transcription"] = ""
            result["speech_rate_wpm"] = None

        # 8. Layer 6: Watermark Verification
        wm_found = False
        wm_conf = 0.0
        wm_id = None
        try:
            wm_res = watermark_decoder.detect_mvp_watermark(file_path, frequency=19000.0)
            if wm_res and wm_res.get("found"):
                wm_found = True
                wm_conf = float(wm_res.get("confidence", 0.0))
                wm_id = wm_res.get("watermark_id")
        except Exception:
            pass
        result["layer6_watermark_found"] = wm_found
        result["layer6_watermark_confidence"] = round(wm_conf, 4)
        result["layer6_watermark_id"] = wm_id or ""

        # 9. Dynamic Layer Weight Reallocation
        # On unwatermarked organic speech (human benchmark), absence of a watermark is natural
        # and does not penalize authenticity. Watermark acts as a cryptographic booster when present.
        weights = {
            "l1": {"score": l1_auth_score, "weight": 0.25},
            "l3": {"score": l3_auth_score, "weight": 0.20},
            "l4": {"score": l4_auth_score, "weight": 0.20},
        }
        if l2_auth_score is not None:
            weights["l2"] = {"score": l2_auth_score, "weight": 0.20}
        else:
            weights["l1"]["weight"] += 0.10
            weights["l3"]["weight"] += 0.10

        if l5_auth_score is not None:
            weights["l5"] = {"score": l5_auth_score, "weight": 0.15}
        else:
            weights["l1"]["weight"] += 0.10
            weights["l4"]["weight"] += 0.05

        if wm_found and wm_conf >= 0.85:
            weights["l6"] = {"score": 1.0, "weight": 0.30}
            weights["l1"]["weight"] = 0.20
            weights["l2"]["weight"] = 0.15
            weights["l3"]["weight"] = 0.15
            weights["l4"]["weight"] = 0.10
            weights["l5"]["weight"] = 0.10

        adj_weights = TelephoneChannelPreprocessor.adjust_layer_weights(weights, is_telephony=is_telephony)

        # Calculate overall weighted authenticity score
        total_weight = 0.0
        weighted_sum = 0.0
        for layer_k, layer_data in adj_weights.items():
            w = layer_data.get("weight", 0.0)
            s = layer_data.get("score", 0.5)
            if w > 0:
                weighted_sum += w * s
                total_weight += w

        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.5
        result["overall_authenticity_score"] = round(overall_score, 4)

        # Verdict assignment
        if wm_found and wm_conf >= 0.85:
            verdict = "Authentic (Cryptographically Watermarked)"
            is_synthetic = False
        elif overall_score >= 0.70:
            verdict = "Authentic Human Voice"
            is_synthetic = False
        elif overall_score >= threshold:
            verdict = "Authentic (Borderline / Natural Variations)"
            is_synthetic = False
        elif overall_score >= 0.25:
            verdict = "Suspicious (Likely Synthetic)"
            is_synthetic = True
        else:
            verdict = "High Confidence Deepfake / Synthetic"
            is_synthetic = True

        result["verdict"] = verdict
        result["is_synthetic"] = is_synthetic

        # Accuracy computation against Ground Truth
        if ground_truth.lower() == "human":
            is_correct = (not is_synthetic)
        elif ground_truth.lower() in {"synthetic", "fake", "deepfake"}:
            is_correct = bool(is_synthetic)
        else:
            is_correct = None
        result["is_correct"] = is_correct

        # 10. Partial Fake Localization (0.5s resolution)
        try:
            loc_res = localizer.analyze_audio(audio_16k, sr=16000)
            result["partial_fake_verdict"] = loc_res.get("clip_verdict", "UNKNOWN")
            segments = loc_res.get("segments", [])
            spliced_ranges = []
            for seg in segments:
                if seg.get("is_fake", False):
                    spliced_ranges.append(f"{seg['start_sec']:.1f}s-{seg['end_sec']:.1f}s")
            result["spliced_segments"] = "; ".join(spliced_ranges) if spliced_ranges else "None"
        except Exception:
            result["partial_fake_verdict"] = "N/A"
            result["spliced_segments"] = "N/A"

    except Exception as exc:
        result["error"] = str(exc)
        result["verdict"] = "Error"
        result["is_synthetic"] = None
        result["is_correct"] = False
        result["overall_authenticity_score"] = 0.0

    result["processing_time_ms"] = round((time.time() - start_t) * 1000, 1)
    return result


def find_audio_files(directory: str, recursive: bool = True) -> List[str]:
    """Find all supported audio files in a directory."""
    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    pattern = "**/*" if recursive else "*"
    audio_files = []
    for p in dir_path.glob(pattern):
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS:
            audio_files.append(str(p.resolve()))

    return sorted(audio_files)


def load_processed_file_paths(csv_path: Path) -> Set[str]:
    """Read existing file_path entries from CSV for resume capability."""
    processed = set()
    if not csv_path.exists():
        return processed

    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "file_path" in row and row["file_path"]:
                    processed.add(row["file_path"])
    except Exception:
        pass
    return processed


def print_batch_report(
    batch_num: int,
    total_batches: int,
    batch_items: List[Dict[str, Any]],
    cumulative_items: List[Dict[str, Any]],
    total_dataset_files: int,
    ground_truth: str,
    batch_elapsed: float,
    total_elapsed: float
):
    """Display rich structured performance and accuracy report after each batch."""
    batch_valid = [r for r in batch_items if r.get("error") is None]
    batch_correct = sum(1 for r in batch_valid if r.get("is_correct") is True)
    batch_accuracy = (batch_correct / max(1, len(batch_valid))) * 100.0
    batch_avg_score = np.mean([r["overall_authenticity_score"] for r in batch_valid]) if batch_valid else 0.0

    cum_valid = [r for r in cumulative_items if r.get("error") is None]
    cum_correct = sum(1 for r in cum_valid if r.get("is_correct") is True)
    cum_accuracy = (cum_correct / max(1, len(cum_valid))) * 100.0
    cum_avg_score = np.mean([r["overall_authenticity_score"] for r in cum_valid]) if cum_valid else 0.0

    cum_false_alarms = sum(1 for r in cum_valid if r.get("is_synthetic") is True) if ground_truth.lower() == "human" else 0
    cum_false_alarm_rate = (cum_false_alarms / max(1, len(cum_valid))) * 100.0

    print("\n" + "=" * 76)
    print(f"  BATCH {batch_num} OF {total_batches} RESULTS ({len(batch_items)} files processed in {batch_elapsed:.1f}s)")
    print("=" * 76)
    print(f"  Ground Truth Benchmark:     {ground_truth.upper()} VOICES")
    print(f"  Batch Authenticity Score:   {batch_avg_score:.4f} (Avg across batch)")
    print(f"  BATCH ACCURACY:             {batch_accuracy:.2f}% ({batch_correct}/{len(batch_valid)} correctly verified as human)")
    if ground_truth.lower() == "human":
        batch_fa = len(batch_valid) - batch_correct
        print(f"  Batch False Alarms (Fake):  {batch_fa} ({batch_fa / max(1, len(batch_valid)) * 100:.1f}%)")

    print("  " + "-" * 72)
    print("  CUMULATIVE SYSTEM PERFORMANCE SO FAR:")
    print("  " + "-" * 72)
    print(f"  Total Processed:            {len(cumulative_items)} / {total_dataset_files} files ({(len(cumulative_items) / total_dataset_files) * 100:.1f}%)")
    print(f"  CUMULATIVE ACCURACY:        {cum_accuracy:.2f}% ({cum_correct}/{len(cum_valid)} correct)")
    if ground_truth.lower() == "human":
        print(f"  False Alarm Rate (FPR):     {cum_false_alarm_rate:.2f}% ({cum_false_alarms}/{len(cum_valid)} flagged as synthetic)")
    print(f"  Mean Authenticity Score:    {cum_avg_score:.4f}")
    print(f"  Cumulative Time Elapsed:    {total_elapsed:.1f}s ({total_elapsed / max(1, len(cumulative_items)):.2f}s per file)")
    print("=" * 76 + "\n")


def batch_evaluate_dataset(
    input_dir: str,
    output_csv: str,
    batch_size: int = 50,
    ground_truth: str = "human",
    threshold: float = 0.45,
    workers: int = 4,
    recursive: bool = True,
    max_files: Optional[int] = None,
    resume: bool = True,
    reference_speaker_path: Optional[str] = None
):
    """Batch evaluate audio dataset with per-batch metrics and live accuracy reports."""
    print("=" * 76)
    print("  Whicoustic AUDIO DATASET BATCH EVALUATION & ACCURACY BENCHMARK")
    print(f"  Target Directory:  {input_dir}")
    print(f"  Batch Size:        {batch_size} files / batch")
    print(f"  Ground Truth:      {ground_truth.upper()} (All files are human voices)")
    print(f"  Output CSV:        {output_csv}")
    print("=" * 76)

    audio_files = find_audio_files(input_dir, recursive=recursive)
    if not audio_files:
        print(f"\n[!] No audio files ({', '.join(AUDIO_EXTENSIONS)}) found in {input_dir}")
        print("    Please ensure the download has completed or check the folder path.")
        return

    if max_files and len(audio_files) > max_files:
        print(f"[*] Found {len(audio_files)} files; limiting to first {max_files} files as requested.")
        audio_files = audio_files[:max_files]
    else:
        print(f"[*] Total dataset audio files discovered: {len(audio_files)}")

    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Resume support: skip already processed files
    already_processed = set()
    if resume and out_path.exists():
        already_processed = load_processed_file_paths(out_path)
        if already_processed:
            print(f"[*] Found existing CSV with {len(already_processed)} previously processed files. Resuming...")
            audio_files = [f for f in audio_files if f not in already_processed]
            if not audio_files:
                print("[*] All files have already been processed in the existing CSV file!")
                return
            print(f"[*] Remaining files to evaluate: {len(audio_files)}")

    # Initialize services
    print("\n[*] Initializing 6-Layer Deepfake Defense and Signal Analysis Services...")
    antispoof = AntiSpoofDetector()
    prosody = ProsodyService()
    paralinguistic = ParalinguisticService()
    watermark = WatermarkDecoder()
    telephony = TelephoneChannelPreprocessor(target_sr=16000)
    localizer = PartialFakeLocalizer(sample_rate=16000)
    speaker_verifier = SpeakerVerifier()
    semantic_service = SemanticService()

    # Determine file write mode
    file_exists = out_path.exists() and out_path.stat().st_size > 0
    write_header = not file_exists

    # Split audio files into batches
    total_files = len(audio_files)
    num_batches = int(np.ceil(total_files / batch_size))
    print(f"[*] Organized into {num_batches} batch(es) of up to {batch_size} files each.\n")

    cumulative_results: List[Dict[str, Any]] = []
    overall_start_time = time.time()

    with open(out_path, mode="a" if file_exists else "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
            f.flush()

        for b_idx in range(num_batches):
            batch_num = b_idx + 1
            start_i = b_idx * batch_size
            end_i = min(start_i + batch_size, total_files)
            batch_files = audio_files[start_i:end_i]

            batch_results: List[Dict[str, Any]] = []
            batch_start_time = time.time()

            print(f"--- Processing Batch {batch_num}/{num_batches} ({len(batch_files)} files in parallel with {workers} workers) ---")

            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_idx = {
                    executor.submit(
                        analyze_single_audio,
                        file_p,
                        antispoof,
                        prosody,
                        paralinguistic,
                        watermark,
                        telephony,
                        localizer,
                        ground_truth,
                        threshold,
                        reference_speaker_path,
                        speaker_verifier,
                        semantic_service
                    ): (f_idx, file_p)
                    for f_idx, file_p in enumerate(batch_files, 1)
                }

                for future in future_to_idx:
                    f_idx, file_p = future_to_idx[future]
                    fname = os.path.basename(file_p)
                    global_idx = start_i + f_idx
                    print(f"  [{global_idx:>4}/{total_files:<4}] {fname[:34]:<36} ... ", end="", flush=True)

                    res = future.result()

                    # Write immediately to CSV so no data is lost
                    writer.writerow(res)
                    f.flush()

                    batch_results.append(res)
                    cumulative_results.append(res)

                    if res.get("error"):
                        print(f"[ERROR: {res['error'][:25]}]")
                    else:
                        score = res.get("overall_authenticity_score", 0.0)
                        is_correct = res.get("is_correct")
                        tag = "CORRECT (HUMAN)" if is_correct else "MISCLASSIFIED"
                        ms = res.get("processing_time_ms", 0.0)
                        print(f"Score={score:.2f} [{tag}] ({ms:.0f}ms)")

            batch_elapsed = time.time() - batch_start_time
            total_elapsed = time.time() - overall_start_time

            # Print per-batch report and cumulative accuracy
            print_batch_report(
                batch_num=batch_num,
                total_batches=num_batches,
                batch_items=batch_results,
                cumulative_items=cumulative_results,
                total_dataset_files=total_files,
                ground_truth=ground_truth,
                batch_elapsed=batch_elapsed,
                total_elapsed=total_elapsed
            )

    print(f"\n[DONE] Batch evaluation completed! Complete results saved to: {out_path.resolve()}\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluate audio dataset with Whicoustic defense layers and export CSV.")
    parser.add_argument("--input-dir", "-i", type=str, default="data", help="Directory containing audio files.")
    parser.add_argument("--output-csv", "-o", type=str, default="dataset_evaluation_results.csv", help="Path for output CSV file.")
    parser.add_argument("--batch-size", "-b", type=int, default=50, help="Number of files per batch (default: 50).")
    parser.add_argument("--ground-truth", "-g", type=str, default="human", choices=["human", "synthetic", "mixed"], help="Ground truth for accuracy calculation.")
    parser.add_argument("--threshold", "-t", type=float, default=0.45, help="Authenticity threshold (default: 0.45).")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Number of parallel worker threads (default: 4).")
    parser.add_argument("--non-recursive", action="store_true", help="Do not search subdirectories.")
    parser.add_argument("--no-resume", action="store_true", help="Do not resume; re-process existing files.")
    parser.add_argument("--max-files", "-m", type=int, default=None, help="Maximum number of files to evaluate.")
    parser.add_argument("--reference-audio", "-r", type=str, default=None, help="Optional reference audio for speaker verification.")

    args = parser.parse_args()

    batch_evaluate_dataset(
        input_dir=args.input_dir,
        output_csv=args.output_csv,
        batch_size=args.batch_size,
        ground_truth=args.ground_truth,
        threshold=args.threshold,
        workers=args.workers,
        recursive=not args.non_recursive,
        resume=not args.no_resume,
        max_files=args.max_files,
        reference_speaker_path=args.reference_audio
    )


if __name__ == "__main__":
    main()
