"""
Unit tests for backend voice detection API service and route integration.
"""

import pytest
import numpy as np
from backend.services.voice_detector import detect_ai_voice


def test_detect_ai_voice_api():
    waveform = np.random.randn(64600).astype(np.float32)
    result = detect_ai_voice(waveform)

    assert isinstance(result, dict)
    assert "is_ai_voice" in result
    assert "confidence" in result
    assert "voice_risk" in result
    assert "deepfake_score" in result
    assert "embedding_drift_score" in result
    assert "model_version" in result
    assert result["embedding_drift_score"] is None
    assert 0 <= result["voice_risk"] <= 100


def test_detect_ai_voice_empty():
    result = detect_ai_voice(np.array([], dtype=np.float32))
    assert result["is_ai_voice"] is False
    assert result["voice_risk"] == 0
    assert result["prediction"] == "UNCERTAIN"
