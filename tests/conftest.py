"""Test configuration and shared fixtures for VoxShield Member 1."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_wav(tmp_path):
    """Create a valid sample WAV file for testing."""
    import numpy as np
    import soundfile as sf

    sr = 16000
    duration = 3.0
    t = np.linspace(0, duration, int(sr * duration), dtype=np.float32)
    # Sine wave at 440Hz + some noise
    waveform = 0.3 * np.sin(2 * np.pi * 440 * t) + 0.05 * np.random.randn(len(t)).astype(np.float32)
    waveform = waveform / np.max(np.abs(waveform)) * 0.9

    wav_path = tmp_path / "test_audio.wav"
    sf.write(str(wav_path), waveform, sr)
    return wav_path


@pytest.fixture
def short_wav(tmp_path):
    """Create a WAV file that is too short for analysis."""
    import numpy as np
    import soundfile as sf

    waveform = np.random.randn(100).astype(np.float32) * 0.1
    wav_path = tmp_path / "short_audio.wav"
    sf.write(str(wav_path), waveform, 16000)
    return wav_path


@pytest.fixture
def silent_wav(tmp_path):
    """Create a silent WAV file."""
    import numpy as np
    import soundfile as sf

    waveform = np.zeros(48000, dtype=np.float32)
    wav_path = tmp_path / "silent_audio.wav"
    sf.write(str(wav_path), waveform, 16000)
    return wav_path


@pytest.fixture
def long_wav(tmp_path):
    """Create a long WAV file for multi-segment testing."""
    import numpy as np
    import soundfile as sf

    sr = 16000
    duration = 12.0
    t = np.linspace(0, duration, int(sr * duration), dtype=np.float32)
    waveform = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    wav_path = tmp_path / "long_audio.wav"
    sf.write(str(wav_path), waveform, sr)
    return wav_path


@pytest.fixture
def test_config():
    """Load project config for testing."""
    from backend.utils.config import load_config
    return load_config()


@pytest.fixture
def detector(test_config):
    """Create a VoiceDetector with test config."""
    from backend.services.voice_detector import VoiceDetector
    return VoiceDetector(test_config)
