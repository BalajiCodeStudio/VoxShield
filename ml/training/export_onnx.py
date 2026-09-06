"""
ONNX Export script for VoxShield RawTFNet model.
Exports PyTorch RawTFNet to ONNX FP32 format and verifies parity against PyTorch.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import onnx
import onnxruntime as ort

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "ml"))

from ml.inference.models.rawtfnet_net import RawTFNet


def export_rawtfnet_to_onnx(
    checkpoint_path: str,
    output_onnx_path: str,
    opset_version: int = 17,
) -> bool:
    """Exports RawTFNet state_dict checkpoint to ONNX."""
    print(f"[*] Loading PyTorch model from {checkpoint_path}...")
    net = RawTFNet(sample_rate=16000)
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    net.load_state_dict(state, strict=False)
    net.eval()

    # Dummy input: (1, 64600) float32 audio waveform
    dummy_input = torch.randn(1, 64600, dtype=torch.float32)

    print(f"[*] Exporting to ONNX at {output_onnx_path} (Opset {opset_version})...")
    os.makedirs(os.path.dirname(os.path.abspath(output_onnx_path)), exist_ok=True)

    torch.onnx.export(
        net,
        dummy_input,
        output_onnx_path,
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=["wav"],
        output_names=["logits"],
        dynamic_axes={
            "wav": {0: "batch"},
            "logits": {0: "batch"},
        },
    )

    print("[*] Checking exported ONNX model...")
    onnx_model = onnx.load(output_onnx_path)
    onnx.checker.check_model(onnx_model)
    onnx_size_bytes = os.path.getsize(output_onnx_path)
    print(f"[+] ONNX Export Successful! File size: {onnx_size_bytes:,} bytes ({onnx_size_bytes / (1024*1024):.3f} MB)")

    # Test Parity
    with torch.no_grad():
        pt_out = net(dummy_input).numpy()

    sess = ort.InferenceSession(output_onnx_path, providers=["CPUExecutionProvider"])
    ort_out = sess.run(None, {"wav": dummy_input.numpy()})[0]

    max_diff = np.max(np.abs(pt_out - ort_out))
    print(f"[+] Max absolute difference between PyTorch and ONNX: {max_diff:.6e}")
    if max_diff < 1e-4:
        print("[+] PARITY VERIFIED: ONNX outputs match PyTorch within tolerance.")
        return True
    else:
        print(f"[-] WARNING: Parity difference {max_diff:.6e} exceeds 1e-4.")
        return False


if __name__ == "__main__":
    ckpt = PROJECT_ROOT / "ml" / "models" / "lightweight" / "rawtfnet" / "Best_RawTFNet_32.pth"
    out_onnx = PROJECT_ROOT / "ml" / "models" / "lightweight" / "rawtfnet" / "rawtfnet.onnx"
    export_rawtfnet_to_onnx(str(ckpt), str(out_onnx))
