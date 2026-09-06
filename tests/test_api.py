"""Tests for FastAPI /api/voice/analyze endpoint."""
from __future__ import annotations

import io
import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client with a stubbed detector."""
    from unittest.mock import patch, MagicMock
    from backend.services.voice_detector import VoiceDetector

    # Create a mock detector that returns a fixed result for valid audio
    mock_detector = MagicMock(spec=VoiceDetector)
    mock_detector.load_models.return_value = {}
    mock_detector.get_model_status.return_value = {}

    from backend.services.voice_detector import DetectionResult
    mock_result = DetectionResult(
        success=True, prediction="AI_GENERATED", confidence=0.85,
        real_probability=0.15, fake_probability=0.85,
        ensemble_probability=0.85, model_agreement=1.0,
        segments_analyzed=1, processing_time_ms=50.0,
        models={"w2v2_aasist": 0.85}, audio_duration_seconds=3.0,
    )
    mock_detector.predict_file.return_value = mock_result

    with patch("backend.routes.analyze.get_voice_detector", return_value=mock_detector):
        from backend.main import app
        with TestClient(app) as c:
            yield c, mock_detector


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        c, _ = client
        resp = c.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestAnalyzeEndpoint:
    def test_valid_upload(self, client, sample_wav):
        c, mock_det = client
        with open(sample_wav, "rb") as f:
            resp = c.post("/api/voice/analyze", files={"audio": ("test.wav", f, "audio/wav")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["prediction"] in ("REAL", "AI_GENERATED", "UNCERTAIN")
        assert "confidence" in data
        assert "request_id" in data

    def test_unsupported_format(self, client):
        c, _ = client
        resp = c.post("/api/voice/analyze", files={"audio": ("test.xyz", io.BytesIO(b"data"), "application/octet-stream")})
        assert resp.status_code == 400

    def test_missing_audio(self, client):
        c, _ = client
        resp = c.post("/api/voice/analyze")
        assert resp.status_code == 422  # Unprocessable Entity

    def test_file_too_large(self, client):
        c, _ = client
        large_data = b"x" * 30_000_000
        resp = c.post("/api/voice/analyze", files={"audio": ("big.wav", io.BytesIO(large_data), "audio/wav")})
        assert resp.status_code == 413
