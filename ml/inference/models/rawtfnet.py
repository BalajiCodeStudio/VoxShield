"""
RawTFNet model adapter for VoxShield voice deepfake detection.
Encapsulates RawTFNet PyTorch and ONNX Runtime inference, windowing (64,600 samples @ 16kHz),
and probability computation.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import numpy as np
import torch
import torch.nn.functional as F

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

from .rawtfnet_net import RawTFNet

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_WINDOW_SAMPLES = 64600  # 4.0375 seconds @ 16kHz
NUM_CLASSES = 2
CLASS_SPOOF_FAKE = 0
CLASS_BONAFIDE_REAL = 1


def pad_or_crop_waveform(waveform: np.ndarray, target_length: int = DEFAULT_WINDOW_SAMPLES) -> np.ndarray:
    """
    Ensures waveform is 1D float32 of exactly target_length.
    If shorter, tile/repeat the audio to reach target_length.
    If longer, crop the first target_length samples.
    """
    if waveform.ndim > 1:
        waveform = np.mean(waveform, axis=0) if waveform.shape[0] < waveform.shape[1] else np.mean(waveform, axis=1)
    waveform = waveform.astype(np.float32)

    length = len(waveform)
    if length == 0:
        return np.zeros(target_length, dtype=np.float32)

    if length < target_length:
        num_repeats = int(np.ceil(target_length / length))
        waveform = np.tile(waveform, num_repeats)
    
    if len(waveform) > target_length:
        waveform = waveform[:target_length]
    elif len(waveform) < target_length:
        pad_width = target_length - len(waveform)
        waveform = np.pad(waveform, (0, pad_width), mode="constant")

    return np.ascontiguousarray(waveform, dtype=np.float32)


class RawTFNetModel:
    """
    Production adapter for SpeechAntiSpoofingBenchmarks/RawTFNet.
    Provides PyTorch and ONNX runtime inference, parameter introspection, and safety checks.
    """

    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        onnx_path: Optional[str] = None,
        use_onnx: bool = False,
        device: str = "cpu",
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        window_samples: int = DEFAULT_WINDOW_SAMPLES,
    ):
        self.checkpoint_path = checkpoint_path
        self.onnx_path = onnx_path
        self.use_onnx = use_onnx and ONNX_AVAILABLE
        self.device = torch.device(device if torch.cuda.is_available() and device == "cuda" else "cpu")
        self.sample_rate = sample_rate
        self.window_samples = window_samples

        self._net: Optional[RawTFNet] = None
        self._ort_session: Optional[Any] = None
        self._is_loaded: bool = False
        self._num_params: int = 177540
        self._checkpoint_size_bytes: int = 0

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def parameter_count(self) -> int:
        return self._num_params

    @property
    def checkpoint_size_bytes(self) -> int:
        return self._checkpoint_size_bytes

    def load(self, model_path: Optional[str] = None) -> None:
        """
        Loads the model weights into memory ONCE.
        Prefers local checkpoint if provided, falls back to Hugging Face download or ONNX.
        """
        if self._is_loaded:
            logger.debug("RawTFNet model is already loaded in memory.")
            return

        target_path = model_path or self.checkpoint_path
        
        # Default local resolution paths
        if not target_path:
            possible_local_pth = [
                Path(__file__).resolve().parents[2] / "models" / "lightweight" / "rawtfnet" / "Best_RawTFNet_32.pth",
                Path(__file__).resolve().parents[3] / "models" / "lightweight" / "rawtfnet" / "Best_RawTFNet_32.pth",
                Path("ml/models/lightweight/rawtfnet/Best_RawTFNet_32.pth"),
            ]
            for p in possible_local_pth:
                if p.exists():
                    target_path = str(p)
                    break

        # Fallback to huggingface_hub download if not found locally
        if not target_path or not os.path.exists(target_path):
            try:
                from huggingface_hub import hf_hub_download
                logger.info("Fetching RawTFNet weights from Hugging Face hub...")
                target_path = hf_hub_download(
                    repo_id="SpeechAntiSpoofingBenchmarks/RawTFNet",
                    filename="Best_RawTFNet_32.pth",
                )
            except Exception as e:
                logger.warning(f"Failed to fetch Best_RawTFNet_32.pth from HF Hub: {e}")

        # Check if ONNX is requested and available
        if self.use_onnx:
            onnx_target = self.onnx_path
            if not onnx_target:
                possible_onnx = [
                    Path(__file__).resolve().parents[2] / "models" / "lightweight" / "rawtfnet" / "rawtfnet.onnx",
                    Path("ml/models/lightweight/rawtfnet/rawtfnet.onnx"),
                ]
                for p in possible_onnx:
                    if p.exists():
                        onnx_target = str(p)
                        break
            if not onnx_target or not os.path.exists(onnx_target):
                try:
                    from huggingface_hub import hf_hub_download
                    onnx_target = hf_hub_download(
                        repo_id="SpeechAntiSpoofingBenchmarks/RawTFNet",
                        filename="rawtfnet.onnx",
                    )
                except Exception as e:
                    logger.warning(f"Could not download ONNX model: {e}")
                    self.use_onnx = False

            if self.use_onnx and onnx_target and os.path.exists(onnx_target):
                logger.info(f"Loading RawTFNet ONNX Runtime session from {onnx_target}...")
                providers = ["CPUExecutionProvider"]
                self._ort_session = ort.InferenceSession(onnx_target, providers=providers)
                self._checkpoint_size_bytes = os.path.getsize(onnx_target)
                self._is_loaded = True
                logger.info(f"RawTFNet ONNX loaded successfully ({self._checkpoint_size_bytes} bytes).")
                return

        # Load PyTorch model
        if not target_path or not os.path.exists(target_path):
            raise FileNotFoundError(f"RawTFNet checkpoint not found at {target_path}")

        logger.info(f"Loading RawTFNet PyTorch model from {target_path} on {self.device}...")
        net = RawTFNet(sample_rate=self.sample_rate)
        state = torch.load(target_path, map_location=self.device, weights_only=False)
        net.load_state_dict(state, strict=False)
        net.to(self.device)
        net.eval()

        self._net = net
        self._num_params = sum(p.numel() for p in net.parameters())
        self._checkpoint_size_bytes = os.path.getsize(target_path)
        self._is_loaded = True
        logger.info(f"RawTFNet PyTorch loaded successfully. Parameters: {self._num_params:,}, Size: {self._checkpoint_size_bytes} bytes.")

    def predict(self, waveform: np.ndarray) -> Tuple[float, float, np.ndarray]:
        """
        Runs inference on a single 1D waveform chunk.
        
        Returns:
            (fake_probability, real_probability, raw_logits)
            where fake_probability in [0.0, 1.0], real_probability = 1.0 - fake_probability.
        """
        if not self._is_loaded:
            self.load()

        # Window/pad to exactly window_samples
        padded = pad_or_crop_waveform(waveform, target_length=self.window_samples)
        
        if self._ort_session is not None:
            # ONNX Runtime path
            inp = padded[np.newaxis, :]  # shape (1, 64600)
            logits = self._ort_session.run(None, {"wav": inp})[0]  # shape (1, 2)
            logits = logits[0]
            # Softmax
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / np.sum(exp_logits)
            fake_prob = float(probs[CLASS_SPOOF_FAKE])
            real_prob = float(probs[CLASS_BONAFIDE_REAL])
            return fake_prob, real_prob, logits

        if self._net is None:
            raise RuntimeError("RawTFNet model is not initialized.")

        tensor_in = torch.from_numpy(padded).unsqueeze(0).to(self.device, dtype=torch.float32)
        with torch.no_grad():
            logits_tensor = self._net(tensor_in)  # (1, 2)
            probs_tensor = F.softmax(logits_tensor, dim=1)

        logits = logits_tensor.squeeze(0).cpu().numpy()
        probs = probs_tensor.squeeze(0).cpu().numpy()

        fake_prob = float(probs[CLASS_SPOOF_FAKE])
        real_prob = float(probs[CLASS_BONAFIDE_REAL])
        return fake_prob, real_prob, logits

    def extract_embedding(self, waveform: np.ndarray) -> Optional[np.ndarray]:
        """
        Extracts embedding representation if supported.
        RawTFNet is a classification network ending in pooling over separable conv channels.
        Per strict specification: if embedding extraction is not reliably supported/defined,
        return None without fabricating values.
        """
        return None

    def get_metadata(self) -> Dict[str, Any]:
        """Returns introspected model metadata."""
        return {
            "model_name": "RawTFNet",
            "repository": "SpeechAntiSpoofingBenchmarks/RawTFNet",
            "paper": "RawTFNet: A Lightweight CNN Architecture for Speech Anti-spoofing (Xiao et al., 2025)",
            "parameter_count": self._num_params,
            "checkpoint_size_bytes": self._checkpoint_size_bytes,
            "checkpoint_size_mb": round(self._checkpoint_size_bytes / (1024 * 1024), 3),
            "sample_rate_hz": self.sample_rate,
            "window_samples": self.window_samples,
            "window_seconds": round(self.window_samples / self.sample_rate, 4),
            "num_classes": NUM_CLASSES,
            "class_mapping": {
                "0": "spoof / AI_GENERATED",
                "1": "bonafide / REAL",
            },
            "onnx_available": ONNX_AVAILABLE,
            "active_backend": "onnxruntime" if self._ort_session is not None else "pytorch",
            "device": str(self.device),
        }
