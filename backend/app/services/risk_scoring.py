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


import time


def assign_layer_status(layer_name: str, layer_dict: Dict[str, Any]) -> str:
    """
    Determine explicit pass / anomaly / fail status per layer matching
    PROJECT.md § Frontend ↔ Backend Forensic WebSocket Stream and
    Milestone 4 layer status matrix.
    """
    if not isinstance(layer_dict, dict):
        return "anomaly"

    # If error occurred:
    if "error" in layer_dict:
        return "anomaly"

    # Disabled / telephony channels
    status_raw = layer_dict.get("status")
    if status_raw in {"disabled_telephony", "disabled", "skipped"}:
        return "pass"

    score = layer_dict.get("score")
    if score is None:
        score = layer_dict.get("authenticity_score")
    if score is None:
        score = 0.5
    score = float(score)

    if layer_name in {"anti_spoof", "layer1_antispoof"}:
        osm = layer_dict.get("open_source_model", {})
        if isinstance(osm.get("fake_probability"), (int, float)) and osm["fake_probability"] >= 0.85:
            return "fail"
        spoof = layer_dict.get("spoof_score")
        if spoof is not None and float(spoof) >= 0.60:
            return "fail"
        if score >= 0.70:
            return "pass"
        elif score >= 0.40:
            return "anomaly"
        else:
            return "fail"

    elif layer_name in {"speaker_consistency", "layer2_speaker_consistency"}:
        sim = layer_dict.get("cosine_similarity", score)
        if sim >= 0.75:
            return "pass"
        elif sim >= 0.50:
            return "anomaly"
        else:
            return "fail"

    elif layer_name in {"prosody", "layer3_prosody"}:
        if score >= 0.65:
            return "pass"
        elif score >= 0.40:
            return "anomaly"
        else:
            return "fail"

    elif layer_name in {"paralinguistic", "layer4_paralinguistic"}:
        if score >= 0.60:
            return "pass"
        elif score >= 0.35:
            return "anomaly"
        else:
            return "fail"

    elif layer_name in {"semantic", "layer5_semantic"}:
        if score >= 0.65:
            return "pass"
        elif score >= 0.40:
            return "anomaly"
        else:
            return "fail"

    elif layer_name in {"watermark", "layer6_watermark"}:
        if layer_dict.get("tampering_detected", False):
            return "fail"
        if layer_dict.get("signature_valid") is False:
            return "fail"
        return "pass"

    return "pass" if score >= 0.60 else ("anomaly" if score >= 0.40 else "fail")


def combine_layer_results(
    layer_results: Dict[str, Any],
    weights: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute the final weighted authenticity score, combined risk score,
    and 6-layer pass/anomaly/fail defense telemetry.

    Args:
        layer_results: Dict mapping layer keys to their raw result dicts.
        weights: Dict mapping weight keys to {"score": float, "weight": float}.

    Returns:
        Dict conforming to PROJECT.md § Frontend ↔ Backend Forensic WebSocket Stream:
          - timestamp (float)
          - combined_risk_score (float, 0-1)
          - overall_authenticity_score (float, 0–1, higher = more authentic)
          - verdict (str: 'AUTHENTIC' | 'SUSPICIOUS' | 'SYNTHETIC')
          - detailed_verdict (str)
          - is_authentic (bool)
          - confidence (float)
          - layers (dict with anti_spoof, speaker_consistency, prosody,
                    paralinguistic, semantic, watermark, each with status)
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
    watermark_found = (
        layer_results.get("layer6_watermark", {}).get("found", False)
        or layer_results.get("watermark", {}).get("found", False)
        or layer_results.get("layer6_watermark", {}).get("detected", False)
        or layer_results.get("watermark", {}).get("detected", False)
    )
    if watermark_found:
        final_authenticity = 0.0

    model_result = (
        layer_results.get("layer1_antispoof", {}).get("open_source_model", {})
        or layer_results.get("anti_spoof", {}).get("open_source_model", {})
    )
    model_fake_probability = model_result.get("fake_probability")
    high_confidence_model_fake = (
        isinstance(model_fake_probability, (int, float))
        and model_fake_probability >= 0.85
    )
    if high_confidence_model_fake:
        final_authenticity = min(final_authenticity, 0.25)

    # Detailed human-readable verdict
    if watermark_found:
        detailed_verdict = "Deepfake (Watermarked Synthetic)"
    elif high_confidence_model_fake:
        detailed_verdict = "Deepfake (Open-Source Model)"
    elif final_authenticity > 0.8:
        detailed_verdict = "Authentic (Human)"
    elif final_authenticity > 0.6:
        detailed_verdict = "Likely Human"
    elif final_authenticity > 0.4:
        detailed_verdict = "Unverified / Insufficient Evidence"
    elif final_authenticity > 0.2:
        detailed_verdict = "Suspicious (Likely Synthetic)"
    else:
        detailed_verdict = "Deepfake (Synthetic)"

    # Contract verdict: "AUTHENTIC" | "SUSPICIOUS" | "SYNTHETIC"
    if watermark_found or high_confidence_model_fake or final_authenticity < 0.40:
        contract_verdict = "SYNTHETIC"
    elif final_authenticity >= 0.65:
        contract_verdict = "AUTHENTIC"
    else:
        contract_verdict = "SUSPICIOUS"

    # Standardize 6 defense layers with explicit pass / anomaly / fail status
    layer_mapping = {
        "anti_spoof": layer_results.get("anti_spoof") or layer_results.get("layer1_antispoof") or {},
        "speaker_consistency": layer_results.get("speaker_consistency") or layer_results.get("layer2_speaker_consistency") or {},
        "prosody": layer_results.get("prosody") or layer_results.get("layer3_prosody") or {},
        "paralinguistic": layer_results.get("paralinguistic") or layer_results.get("layer4_paralinguistic") or {},
        "semantic": layer_results.get("semantic") or layer_results.get("layer5_semantic") or {},
        "watermark": layer_results.get("watermark") or layer_results.get("layer6_watermark") or {},
    }

    standardized_layers: Dict[str, Any] = {}
    for layer_name, data in layer_mapping.items():
        layer_dict = dict(data) if isinstance(data, dict) else {"value": data}
        layer_dict["status"] = assign_layer_status(layer_name, layer_dict)
        if "score" not in layer_dict and "authenticity_score" in layer_dict:
            layer_dict["score"] = layer_dict["authenticity_score"]
        standardized_layers[layer_name] = layer_dict

    # Populate legacy aliases for seamless backward compatibility
    standardized_layers["layer1_antispoof"] = standardized_layers["anti_spoof"]
    standardized_layers["layer2_speaker_consistency"] = standardized_layers["speaker_consistency"]
    standardized_layers["layer3_prosody"] = standardized_layers["prosody"]
    standardized_layers["layer4_paralinguistic"] = standardized_layers["paralinguistic"]
    standardized_layers["layer5_semantic"] = standardized_layers["semantic"]
    standardized_layers["layer6_watermark"] = standardized_layers["watermark"]

    combined_risk = round(max(0.0, min(1.0, 1.0 - final_authenticity)), 4)

    return {
        "timestamp": time.time(),
        "combined_risk_score": combined_risk,
        "overall_authenticity_score": round(final_authenticity, 4),
        "verdict": contract_verdict,
        "detailed_verdict": detailed_verdict,
        "is_authentic": bool(
            final_authenticity > 0.5
            and not watermark_found
            and not high_confidence_model_fake
        ),
        "confidence": round(total_weight, 4),
        "layers": sanitize_numpy(standardized_layers),
        "weights_used": sanitize_numpy(weights),
    }
