"""
Audio utilities for VoxShield Member 1 (Voice Deepfake Detection).
Supports loading WAV, MP3, M4A, FLAC, OGG from bytes or file paths,
mono conversion, 16 kHz resampling, float32 normalization, and Silero VAD / Energy VAD.
"""

from __future__ import annotations

import io
import os
import logging
import tempfile
from typing import List, Tuple, Optional, Union

import numpy as np
import soundfile as sf
import librosa
import torch

logger = logging.getLogger(__name__)

TARGET_SAMPLE_RATE = 16000
MIN_AUDIO_DURATION_SECONDS = 0.25  # Minimum duration to analyze
SILENCE_ENERGY_THRESHOLD = 1e-4

# Lazy global cache for Silero VAD
_SILERO_VAD_MODEL = None
_SILERO_VAD_UTILS = None


def get_silero_vad():
    """Lazy loads Silero VAD model ONCE into memory if available locally, else falls back immediately."""
    global _SILERO_VAD_MODEL, _SILERO_VAD_UTILS
    if _SILERO_VAD_MODEL is None:
        hub_dir = torch.hub.get_dir()
        local_repo = os.path.join(hub_dir, "snakers4_silero-vad_master")
        if os.path.exists(local_repo):
            try:
                model, utils = torch.hub.load(
                    repo_or_dir=local_repo,
                    model="silero_vad",
                    source="local",
                    trust_repo=True,
                )
                _SILERO_VAD_MODEL = model
                _SILERO_VAD_UTILS = utils
                logger.info("Local Silero VAD model loaded successfully.")
                return _SILERO_VAD_MODEL, _SILERO_VAD_UTILS
            except Exception as e:
                logger.debug(f"Failed to load local Silero VAD: {e}")
        _SILERO_VAD_MODEL = False
        _SILERO_VAD_UTILS = None
    return _SILERO_VAD_MODEL, _SILERO_VAD_UTILS


def load_and_preprocess_audio(
    audio_input: Union[bytes, str, np.ndarray],
    target_sr: int = TARGET_SAMPLE_RATE,
    normalize: bool = True,
) -> np.ndarray:
    """
    Loads audio from bytes, file path, or numpy array.
    Converts to mono float32, resamples to target_sr (default 16 kHz), and normalizes peak amplitude.
    
    Handles WAV, MP3, M4A, FLAC, OGG formats gracefully.
    """
    if audio_input is None:
        raise ValueError("Audio input is None.")

    # 1. If already a numpy array
    if isinstance(audio_input, np.ndarray):
        y = audio_input.astype(np.float32)
        if y.ndim > 1:
            y = np.mean(y, axis=0) if y.shape[0] < y.shape[1] else np.mean(y, axis=1)
        if normalize and len(y) > 0:
            max_val = np.max(np.abs(y))
            if max_val > 1e-6:
                y = y / max_val
        return np.ascontiguousarray(y, dtype=np.float32)

    # 2. If bytes
    if isinstance(audio_input, bytes):
        if len(audio_input) == 0:
            raise ValueError("Audio byte buffer is empty.")

        # Attempt in-memory decoding with soundfile first (fastest)
        try:
            bio = io.BytesIO(audio_input)
            data, sr = sf.read(bio, dtype="float32")
            if data.ndim > 1:
                data = np.mean(data, axis=1)
            if sr != target_sr:
                data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)
            if normalize and len(data) > 0:
                max_val = np.max(np.abs(data))
                if max_val > 1e-6:
                    data = data / max_val
            return np.ascontiguousarray(data, dtype=np.float32)
        except Exception:
            # Fallback to tempfile with librosa for container formats (MP3, M4A, OGG)
            fd, temp_path = tempfile.mkstemp(suffix=".tmp")
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(audio_input)
                y, sr = librosa.load(temp_path, sr=target_sr, mono=True)
                if normalize and len(y) > 0:
                    max_val = np.max(np.abs(y))
                    if max_val > 1e-6:
                        y = y / max_val
                return np.ascontiguousarray(y, dtype=np.float32)
            except Exception as e:
                logger.error(f"Error decoding audio bytes: {e}")
                raise ValueError(f"Could not decode audio file. Ensure valid WAV, MP3, M4A, FLAC, or OGG format: {e}")
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

    # 3. If file path
    if isinstance(audio_input, (str, os.PathLike)):
        path_str = str(audio_input)
        if not os.path.exists(path_str):
            raise FileNotFoundError(f"Audio file not found: {path_str}")
        try:
            y, sr = librosa.load(path_str, sr=target_sr, mono=True)
            if normalize and len(y) > 0:
                max_val = np.max(np.abs(y))
                if max_val > 1e-6:
                    y = y / max_val
            return np.ascontiguousarray(y, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error loading audio file {path_str}: {e}")
            raise ValueError(f"Could not decode audio file at {path_str}: {e}")

    raise TypeError(f"Unsupported audio input type: {type(audio_input)}")


def apply_energy_vad(
    waveform: np.ndarray,
    sr: int = TARGET_SAMPLE_RATE,
    frame_ms: int = 30,
    energy_threshold: float = 0.005,
) -> List[Tuple[int, int]]:
    """
    Fast energy-based Voice Activity Detection fallback.
    Returns list of (start_sample, end_sample) speech intervals.
    """
    frame_length = int(sr * frame_ms / 1000)
    hop_length = frame_length // 2

    if len(waveform) < frame_length:
        if np.max(np.abs(waveform)) > energy_threshold:
            return [(0, len(waveform))]
        return []

    # Frame energy
    frames = librosa.util.frame(waveform, frame_length=frame_length, hop_length=hop_length)
    energy = np.mean(frames ** 2, axis=0)

    speech_frames = np.where(energy > (energy_threshold ** 2))[0]
    if len(speech_frames) == 0:
        return []

    # Group continuous frames
    intervals = []
    start_frame = speech_frames[0]
    prev_frame = speech_frames[0]

    for f in speech_frames[1:]:
        if f == prev_frame + 1:
            prev_frame = f
        else:
            intervals.append((start_frame * hop_length, min(len(waveform), prev_frame * hop_length + frame_length)))
            start_frame = f
            prev_frame = f
    intervals.append((start_frame * hop_length, min(len(waveform), prev_frame * hop_length + frame_length)))
    return intervals


def extract_speech_segments(
    waveform: np.ndarray,
    sr: int = TARGET_SAMPLE_RATE,
    min_speech_duration: float = 0.3,
    vad_mode: str = "silero",
) -> List[np.ndarray]:
    """
    Extracts active speech segments using Silero VAD (with energy VAD fallback).
    Concatenates or slices valid speech to eliminate dead silence before RawTFNet inference.
    """
    if len(waveform) == 0:
        return []

    # Check overall amplitude
    if np.max(np.abs(waveform)) < SILENCE_ENERGY_THRESHOLD:
        return []

    intervals = []
    if vad_mode == "silero":
        vad_model, vad_utils = get_silero_vad()
        if vad_model and vad_utils:
            try:
                (get_speech_timestamps, _, read_audio, *_) = vad_utils
                tensor_wav = torch.from_numpy(waveform)
                speech_ts = get_speech_timestamps(
                    tensor_wav,
                    vad_model,
                    sampling_rate=sr,
                    threshold=0.5,
                    min_speech_duration_ms=int(min_speech_duration * 1000),
                )
                for ts in speech_ts:
                    intervals.append((ts["start"], ts["end"]))
            except Exception as e:
                logger.debug(f"Silero VAD execution failed ({e}), falling back to energy VAD.")
                intervals = apply_energy_vad(waveform, sr=sr)
        else:
            intervals = apply_energy_vad(waveform, sr=sr)
    else:
        intervals = apply_energy_vad(waveform, sr=sr)

    # If no speech intervals detected, check if audio has enough RMS energy
    if not intervals:
        rms = np.sqrt(np.mean(waveform ** 2))
        if rms > 0.01:
            return [waveform]
        return []

    segments = []
    min_samples = int(min_speech_duration * sr)
    for start, end in intervals:
        seg = waveform[start:end]
        if len(seg) >= min_samples:
            segments.append(seg)

    return segments
