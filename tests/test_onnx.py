"""Tests for ONNX export and inference parity verification."""
from __future__ import annotations

import numpy as np
import pytest
import torch


class TestOnnxExport:
    def test_export_small_model(self, tmp_path):
        """Test ONNX export with a tiny linear model (no HF dependency)."""
        import onnxruntime as ort

        class TinyModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = torch.nn.Linear(10, 2)

            def forward(self, x):
                return self.linear(x)

        model = TinyModel()
        model.eval()

        onnx_path = tmp_path / "tiny_model.onnx"
        dummy = torch.randn(1, 10)

        torch.onnx.export(
            model, (dummy,), str(onnx_path),
            opset_version=14,
            input_names=["input"],
            output_names=["output"],
        )

        assert onnx_path.exists()
        assert onnx_path.stat().st_size > 0

        # Verify ORT can load and run
        session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        ort_out = session.run(None, {"input": dummy.numpy()})

        with torch.no_grad():
            torch_out = model(dummy).numpy()

        np.testing.assert_allclose(ort_out[0], torch_out, atol=1e-5)

    def test_parity_within_tolerance(self, tmp_path):
        """Test that PyTorch and ONNX outputs are within tolerance."""
        import onnxruntime as ort

        class TinyModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.fc = torch.nn.Linear(20, 2)

            def forward(self, x):
                return self.fc(x)

        model = TinyModel()
        model.eval()

        onnx_path = tmp_path / "parity_model.onnx"
        dummy = torch.randn(2, 20)

        torch.onnx.export(
            model, (dummy,), str(onnx_path),
            opset_version=14,
            input_names=["input"],
            output_names=["output"],
        )

        session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])

        for _ in range(5):
            test_input = torch.randn(2, 20)
            ort_out = session.run(None, {"input": test_input.numpy()})[0]
            with torch.no_grad():
                torch_out = model(test_input).numpy()
            max_diff = np.max(np.abs(ort_out - torch_out))
            assert max_diff < 1e-4, f"Max difference {max_diff} exceeds tolerance"
