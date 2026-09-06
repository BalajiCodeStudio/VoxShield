"""
Unit tests for StreamingVoiceDetector and TemporalSmoother.
"""

import pytest
import numpy as np
from ml.inference.streaming_detector import StreamingVoiceDetector
from ml.inference.postprocessing import TemporalSmoother, aggregate_segment_scores


def test_temporal_smoother_ema():
    smoother = TemporalSmoother(method="ema", alpha=0.5)
    s1 = smoother.update(1.0)
    assert s1 == 1.0
    s2 = smoother.update(0.0)
    assert s2 == 0.5
    s3 = smoother.update(0.0)
    assert s3 == 0.25


def test_aggregate_scores():
    scores = [0.1, 0.2, 0.3, 0.4]
    mean_val = aggregate_segment_scores(scores, method="mean")
    assert abs(mean_val - 0.25) < 1e-4

    max_val = aggregate_segment_scores(scores, method="max")
    assert abs(max_val - 0.4) < 1e-4


def test_streaming_detector_buffer():
    streaming = StreamingVoiceDetector()
    streaming.reset()

    # Feed small chunk (1000 samples)
    chunk = np.random.randn(1000).astype(np.float32)
    res = streaming.feed_audio(chunk)
    assert res is None or res["prediction"] == "UNCERTAIN"

    # Feed enough chunks to trigger window processing
    chunk_large = np.random.randn(64600).astype(np.float32)
    res_window = streaming.feed_audio(chunk_large)
    assert res_window is not None
    assert "deepfake_score" in res_window
    assert res_window["windows_processed"] >= 1
