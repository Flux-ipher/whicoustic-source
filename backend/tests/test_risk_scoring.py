from app.services.risk_scoring import combine_layer_results


def test_high_confidence_open_source_fake_cannot_be_scored_as_human():
    result = combine_layer_results(
        {
            "layer1_antispoof": {
                "score": 0.15,
                "open_source_model": {
                    "fake_probability": 0.92,
                    "engine": "huggingface_wav2vec2",
                },
            },
            "layer3_prosody": {"score": 0.95},
            "layer4_paralinguistic": {"score": 0.95},
            "layer5_semantic": {"score": 0.95},
        },
        {
            "l1": {"score": 0.15, "weight": 0.35},
            "l3": {"score": 0.95, "weight": 0.15},
            "l4": {"score": 0.95, "weight": 0.10},
            "l5": {"score": 0.95, "weight": 0.20},
        },
    )

    assert result["is_authentic"] is False
    assert result["verdict"] == "Deepfake (Open-Source Model)"
    assert result["overall_authenticity_score"] <= 0.25


def test_unavailable_open_source_model_does_not_claim_model_evidence():
    result = combine_layer_results(
        {"layer1_antispoof": {"score": 0.8, "open_source_model": {"engine": "unavailable"}}},
        {"l1": {"score": 0.8, "weight": 0.35}},
    )

    assert result["is_authentic"] is True
    assert "Open-Source Model" not in result["verdict"]
