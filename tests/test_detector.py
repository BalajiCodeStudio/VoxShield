"""
Unit tests for VoxShield VoiceDetector and RawTFNetModel.
"""

import os
import pytest
import numpy as np
from ml.inference.detector import VoiceDetector
from ml.inference.models.rawtfnet import RawTFNetModel


def test_rawtfnet_model_load():
    model = RawTFNetModel()
    model.load()
    assert model.is_loaded is True
    assert model.parameter_count > 0
    assert model.checkpoint_size_bytes > 0


def test_rawtfnet_predict_waveform():
    model = RawTFNetModel()
    model.load()
    dummy = np.random.randn(64600).astype(np.float32)
    fake_p, real_p, logits = model.predict(dummy)

    assert 0.0 <= fake_p <= 1.0
    assert 0.0 <= real_p <= 1.0
    assert abs((fake_p + real_p) - 1.0) < 1e-4
    assert len(logits) == 2


def test_detector_predict_contract():
    detector = VoiceDetector()
    detector.load_model()
    dummy = np.random.randn(64600).astype(np.float32)
    res = detector.predict(dummy)

    assert "prediction" in res
    assert res["prediction"] in ["REAL", "AI_GENERATED", "UNCERTAIN"]
    assert "deepfake_score" in res
    assert "real_probability" in res
    assert "fake_probability" in res
    assert "segments_analyzed" in res
    assert "processing_time_ms" in res
    assert res["model_name"] == "RawTFNet"
    assert res["embedding_drift_score"] is None


def test_detector_short_audio_uncertain():
    detector = VoiceDetector()
    # 0.05 seconds of audio (too short)
    short_audio = np.random.randn(800).astype(np.float32)
    res = detector.predict(short_audio)
    assert res["prediction"] == "UNCERTAIN"
    assert res["deepfake_score"] is None


def test_detector_silent_audio_uncertain():
    detector = VoiceDetector()
    silence = np.zeros(64600, dtype=np.float32)
    res = detector.predict(silence)
    assert res["prediction"] == "UNCERTAIN"
    assert res["deepfake_score"] is None
