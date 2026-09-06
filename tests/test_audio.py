"""
Unit tests for VoxShield audio utilities (backend/utils/audio.py).
"""

import os
import pytest
import numpy as np
import soundfile as sf
import tempfile
from backend.utils.audio import (
    load_and_preprocess_audio,
    extract_speech_segments,
    apply_energy_vad,
    TARGET_SAMPLE_RATE,
)


def test_load_numpy_array():
    # 2-channel 44.1kHz audio array
    sr = 44100
    t = np.linspace(0, 1.0, sr)
    data = np.vstack([np.sin(2 * np.pi * 440 * t), np.cos(2 * np.pi * 440 * t)])
    processed = load_and_preprocess_audio(data, target_sr=16000)
    assert isinstance(processed, np.ndarray)
    assert processed.ndim == 1
    assert len(processed) > 0
    assert np.max(np.abs(processed)) <= 1.0


def test_load_wav_file(tmp_path):
    wav_path = str(tmp_path / "test.wav")
    sr = 16000
    t = np.linspace(0, 1.0, sr)
    audio_data = (np.sin(2 * np.pi * 300 * t) * 0.8).astype(np.float32)
    sf.write(wav_path, audio_data, sr)

    loaded = load_and_preprocess_audio(wav_path, target_sr=16000)
    assert len(loaded) == sr
    assert np.max(np.abs(loaded)) <= 1.0


def test_load_bytes():
    sr = 16000
    t = np.linspace(0, 0.5, int(sr * 0.5))
    audio_data = (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_name = f.name
    try:
        sf.write(temp_name, audio_data, sr)
        with open(temp_name, "rb") as f:
            raw_bytes = f.read()
        loaded = load_and_preprocess_audio(raw_bytes, target_sr=16000)
        assert len(loaded) > 0
        assert isinstance(loaded, np.ndarray)
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)


def test_empty_audio_raises_error():
    with pytest.raises(ValueError):
        load_and_preprocess_audio(b"")


def test_silence_vad():
    silence = np.zeros(16000, dtype=np.float32)
    segments = extract_speech_segments(silence, sr=16000)
    assert len(segments) == 0


def test_speech_vad_detection():
    # 2 seconds of audible sine wave + silence
    sr = 16000
    t = np.linspace(0, 2.0, sr * 2)
    speech = (np.sin(2 * np.pi * 500 * t) * 0.8).astype(np.float32)
    intervals = apply_energy_vad(speech, sr=sr)
    assert len(intervals) > 0
