"""Tests for audio preprocessing, validation, and segmentation."""
from __future__ import annotations

import numpy as np
import pytest
from pathlib import Path


class TestLoadAudio:
    def test_load_wav(self, sample_wav):
        from backend.utils.feature_extraction import load_audio
        waveform, sr = load_audio(sample_wav)
        assert waveform.dtype == np.float32
        assert sr == 16000
        assert len(waveform) > 0

    def test_load_nonexistent(self, tmp_path):
        from backend.utils.feature_extraction import load_audio, AudioCorruptedError
        with pytest.raises(AudioCorruptedError):
            load_audio(tmp_path / "nonexistent.wav")

    def test_load_unsupported_format(self, tmp_path):
        from backend.utils.feature_extraction import load_audio, UnsupportedCodecError
        bad_file = tmp_path / "test.xyz"
        bad_file.write_text("not audio")
        with pytest.raises(UnsupportedCodecError):
            load_audio(bad_file)


class TestValidateAudio:
    def test_too_short(self):
        from backend.utils.feature_extraction import validate_audio, AudioTooShortError
        waveform = np.random.randn(500).astype(np.float32) * 0.1
        with pytest.raises(AudioTooShortError):
            validate_audio(waveform, 16000, min_duration=0.5)

    def test_silent(self):
        from backend.utils.feature_extraction import validate_audio, AudioSilentError
        waveform = np.zeros(16000, dtype=np.float32)
        with pytest.raises(AudioSilentError):
            validate_audio(waveform, 16000, min_rms=1e-4)

    def test_valid(self):
        from backend.utils.feature_extraction import validate_audio
        t = np.linspace(0, 1, 16000, dtype=np.float32)
        waveform = 0.5 * np.sin(2 * np.pi * 440 * t)
        result = validate_audio(waveform, 16000)
        assert len(result) == 16000
        assert np.max(np.abs(result)) <= 1.0


class TestSegmentation:
    def test_short_audio_padded(self):
        from backend.utils.feature_extraction import create_segments
        waveform = np.random.randn(10000).astype(np.float32) * 0.1
        segments, info = create_segments(waveform, 16000, segment_samples=64600, skip_silent=False)
        assert len(segments) >= 1
        assert segments[0].shape == (64600,)

    def test_long_audio_multiple_segments(self):
        from backend.utils.feature_extraction import create_segments
        waveform = np.random.randn(160000).astype(np.float32) * 0.3  # 10s
        segments, info = create_segments(waveform, 16000, segment_samples=64600, hop_samples=32000, skip_silent=False)
        assert info["total_segments"] >= 3

    def test_silent_segments_skipped(self):
        from backend.utils.feature_extraction import create_segments
        waveform = np.zeros(160000, dtype=np.float32)
        with pytest.raises(Exception):
            create_segments(waveform, 16000, segment_samples=64600, skip_silent=True)


class TestPreprocessAudio:
    def test_full_pipeline(self, sample_wav):
        from backend.utils.feature_extraction import preprocess_audio
        buf = preprocess_audio(sample_wav)
        assert buf.sample_rate == 16000
        assert buf.num_segments >= 1
        assert buf.duration_seconds > 0
        for seg in buf.segments:
            assert seg.shape == (64600,)
            assert seg.dtype == np.float32

    def test_error_on_short(self, short_wav):
        from backend.utils.feature_extraction import preprocess_audio, AudioTooShortError
        with pytest.raises(AudioTooShortError):
            preprocess_audio(short_wav)

    def test_error_on_silent(self, silent_wav):
        from backend.utils.feature_extraction import preprocess_audio, AudioSilentError
        with pytest.raises(AudioSilentError):
            preprocess_audio(silent_wav)


class TestClassicalFeatures:
    def test_extract(self):
        from backend.utils.feature_extraction import extract_classical_features
        segment = np.random.randn(64600).astype(np.float32) * 0.1
        features = extract_classical_features(segment, sr=16000)
        assert "rms_energy" in features
        assert "rms_db" in features
        assert "zcr" in features
        assert "spectral_centroid" in features
