"""Tests for VoiceDetector service: classification, aggregation, error handling."""
from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import patch, MagicMock


class TestClassification:
    def test_classify_real(self):
        from backend.services.voice_detector import VoiceDetector
        detector = VoiceDetector({"inference": {"thresholds": {"fake_threshold": 0.5, "real_threshold": 0.5, "uncertain_band": 0.0}}, "ensemble": {"fallback_weights": {}}, "paths": {"threshold_json": "ml/evaluation/threshold.json", "ensemble_weights": "ml/evaluation/ensemble_weights.json"}})
        pred, conf, reason = detector.classify(0.1)
        assert pred == "REAL"
        assert conf == pytest.approx(0.9, abs=0.01)

    def test_classify_fake(self):
        from backend.services.voice_detector import VoiceDetector
        detector = VoiceDetector({"inference": {"thresholds": {"fake_threshold": 0.5, "real_threshold": 0.5, "uncertain_band": 0.0}}, "ensemble": {"fallback_weights": {}}, "paths": {"threshold_json": "ml/evaluation/threshold.json", "ensemble_weights": "ml/evaluation/ensemble_weights.json"}})
        pred, conf, reason = detector.classify(0.9)
        assert pred == "AI_GENERATED"
        assert conf == pytest.approx(0.9, abs=0.01)

    def test_classify_uncertain(self):
        from backend.services.voice_detector import VoiceDetector
        detector = VoiceDetector({"inference": {"thresholds": {"fake_threshold": 0.5, "real_threshold": 0.5, "uncertain_band": 0.1}}, "ensemble": {"fallback_weights": {}}, "paths": {"threshold_json": "ml/evaluation/threshold.json", "ensemble_weights": "ml/evaluation/ensemble_weights.json"}})
        pred, conf, reason = detector.classify(0.5)
        assert pred == "UNCERTAIN"
        assert reason is not None


class TestAggregation:
    def test_weighted_average(self):
        from backend.services.voice_detector import VoiceDetector
        config = {
            "inference": {"thresholds": {"fake_threshold": 0.5, "real_threshold": 0.5, "uncertain_band": 0.0}},
            "ensemble": {"fallback_weights": {"model_a": 0.6, "model_b": 0.4}},
            "paths": {"threshold_json": "ml/evaluation/threshold.json", "ensemble_weights": "ml/evaluation/ensemble_weights.json"},
        }
        detector = VoiceDetector(config)
        ensemble_p, scores = detector.aggregate_predictions({"model_a": 0.8, "model_b": 0.2})
        expected = 0.6 * 0.8 + 0.4 * 0.2
        assert ensemble_p == pytest.approx(expected, abs=0.01)

    def test_single_model(self):
        from backend.services.voice_detector import VoiceDetector
        config = {
            "inference": {"thresholds": {"fake_threshold": 0.5, "real_threshold": 0.5, "uncertain_band": 0.0}},
            "ensemble": {"fallback_weights": {}},
            "paths": {"threshold_json": "ml/evaluation/threshold.json", "ensemble_weights": "ml/evaluation/ensemble_weights.json"},
        }
        detector = VoiceDetector(config)
        ensemble_p, scores = detector.aggregate_predictions({"model_a": 0.75})
        assert ensemble_p == pytest.approx(0.75, abs=0.01)

    def test_no_models_raises(self):
        from backend.services.voice_detector import VoiceDetector
        from backend.models.model_loader import ModelUnavailableError
        config = {
            "inference": {"thresholds": {"fake_threshold": 0.5, "real_threshold": 0.5, "uncertain_band": 0.0}},
            "ensemble": {"fallback_weights": {}},
            "paths": {"threshold_json": "ml/evaluation/threshold.json", "ensemble_weights": "ml/evaluation/ensemble_weights.json"},
        }
        detector = VoiceDetector(config)
        with pytest.raises(ModelUnavailableError):
            detector.aggregate_predictions({})


class TestErrorHandling:
    def test_predict_file_short(self, short_wav):
        from backend.services.voice_detector import VoiceDetector, get_voice_detector
        detector = VoiceDetector({"inference": {"thresholds": {"fake_threshold": 0.5, "real_threshold": 0.5, "uncertain_band": 0.0}}, "ensemble": {"fallback_weights": {}}, "paths": {"cache_dir": ".cache/hf", "threshold_json": "ml/evaluation/threshold.json", "ensemble_weights": "ml/evaluation/ensemble_weights.json"}})
        result = detector.predict_file(short_wav)
        assert not result.success
        assert result.error_code == "AUDIO_TOO_SHORT"

    def test_predict_file_silent(self, silent_wav):
        from backend.services.voice_detector import VoiceDetector
        detector = VoiceDetector({"inference": {"thresholds": {"fake_threshold": 0.5, "real_threshold": 0.5, "uncertain_band": 0.0}}, "ensemble": {"fallback_weights": {}}, "paths": {"cache_dir": ".cache/hf", "threshold_json": "ml/evaluation/threshold.json", "ensemble_weights": "ml/evaluation/ensemble_weights.json"}})
        result = detector.predict_file(silent_wav)
        assert not result.success
        assert result.error_code == "AUDIO_SILENT"
