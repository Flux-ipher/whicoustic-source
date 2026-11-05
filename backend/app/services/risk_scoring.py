"""
Shared risk scoring function — Phase 5 of Real-Time Streaming Detection.

Extracted from the inline logic in api/v1/verify.py (lines 408–427) so that
both the batch /full-analysis endpoint and the streaming StreamSession use
the same weighting, verdict thresholds, and watermark override logic.

Single source of truth: change the weights or thresholds here and both
callers update automatically.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Tuple


def sanitize_numpy(obj: Any) -> Any:
    """Recursively convert numpy scalars / arrays to plain Python types."""
    try:
        import numpy as np  # type: ignore
        if isinstance(obj, np.ndarray):
            return sanitize_numpy(obj.tolist())
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, (np.floating,)):
            v = float(obj)
            return 0.0 if (math.isnan(v) or math.isinf(v)) else v
        if isinstance(obj, (np.integer,)):
            return int(obj)
    except ImportError:
        pass
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return 0.0
    if isinstance(obj, dict):
        return {k: sanitize_numpy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_numpy(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(sanitize_numpy(v) for v in obj)
    return obj


def combine_layer_results(
    layer_results: Dict[str, Any],
    weights: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute the final weighted authenticity score and human-readable verdict.

    Args:
        layer_results: Dict mapping layer keys (e.g. "layer1_antispoof") to
                       their raw result dicts. Populated by the caller.
        weights: Dict mapping weight keys (e.g. "l1") to
                 {"score": float, "weight": float} dicts.
                 Layers that failed or were skipped should not have entries here.

    Returns:
        Dict with:
          - overall_authenticity_score (float, 0–1, higher = more authentic)
          - verdict (str)
          - is_authentic (bool)
          - confidence (float)
          - layers (dict, sanitized)
          - weights_used (dict)
    """
    # Weighted average
    total_weight = sum(w["weight"] for w in weights.values())
    if total_weight > 0:
        final_authenticity = (
            sum(w["score"] * w["weight"] for w in weights.values()) / total_weight
        )
    else:
        final_authenticity = 0.5

    # Clamp
    final_authenticity = float(max(0.0, min(1.0, final_authenticity)))

    # Watermark override — definitive synthetic signal only when a watermark is actually found.
    # Absence of a watermark is not proof of synthetic audio and must not automatically trigger
    # a deepfake verdict for real human speech captured without embedding.
    watermark_found = layer_results.get("layer6_watermark", {}).get("found", False)
    if watermark_found:
        final_authenticity = 0.0

    model_result = layer_results.get("layer1_antispoof", {}).get(
        "open_source_model", {}
    )
    model_fake_probability = model_result.get("fake_probability")
    high_confidence_model_fake = (
        isinstance(model_fake_probability, (int, float))
        and model_fake_probability >= 0.85
    )
    if high_confidence_model_fake:
        # A calibrated specialist model should not be cancelled out by
        # unrelated speaker/prosody heuristics.
        final_authenticity = min(final_authenticity, 0.25)

    # Human-readable verdict
    if watermark_found:
        verdict = "Deepfake (Watermarked Synthetic)"
    elif high_confidence_model_fake:
        verdict = "Deepfake (Open-Source Model)"
    elif final_authenticity > 0.8:
        verdict = "Authentic (Human)"
    elif final_authenticity > 0.6:
        verdict = "Likely Human"
    elif final_authenticity > 0.4:
        verdict = "Unverified / Insufficient Evidence"
    elif final_authenticity > 0.2:
        verdict = "Suspicious (Likely Synthetic)"
    else:
        verdict = "Deepfake (Synthetic)"

    return {
        "overall_authenticity_score": round(final_authenticity, 4),
        "verdict": verdict,
        "is_authentic": bool(
            final_authenticity > 0.5
            and not watermark_found
            and not high_confidence_model_fake
        ),
        "confidence": round(total_weight, 4),  # how many layers contributed
        "layers": sanitize_numpy(layer_results),
        "weights_used": sanitize_numpy(weights),
    }
