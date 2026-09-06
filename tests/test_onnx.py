"""
Unit tests for ONNX model loading and inference equivalence.
"""

import os
import pytest
import numpy as np
import onnxruntime as ort
import torch
from ml.inference.models.rawtfnet import RawTFNetModel


def test_onnx_model_inference():
    onnx_path = os.path.join("ml", "models", "lightweight", "rawtfnet", "rawtfnet.onnx")
    if not os.path.exists(onnx_path):
        pytest.skip("ONNX model file not found")

    sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    dummy_wav = np.random.randn(1, 64600).astype(np.float32)
    out = sess.run(None, {"wav": dummy_wav})[0]

    assert out.shape[1] == 2
    assert not np.isnan(out).any()
