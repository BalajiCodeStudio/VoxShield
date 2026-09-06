"""Shared training utilities: seed setting, device detection, model builders."""
from __future__ import annotations

import logging
import random
from typing import Any

import numpy as np
import torch

logger = logging.getLogger("voxshield.training.common")

SEED = 42


def set_seed(seed: int = SEED) -> None:
    """Set deterministic seed across all random sources."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    logger.info("Set random seed to %d", seed)


def get_device() -> torch.device:
    """Get best available device: CUDA > MPS > CPU."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def build_classifier(backbone_name: str = "facebook/wav2vec2-base", num_labels: int = 2) -> tuple[Any, Any]:
    """Build a wav2vec2-based binary classifier for training.

    Returns (model, processor).
    """
    from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor

    processor = Wav2Vec2FeatureExtractor.from_pretrained(backbone_name)
    model = Wav2Vec2ForSequenceClassification.from_pretrained(
        backbone_name, num_labels=num_labels, problem_type="single_label_classification"
    )
    logger.info("Built classifier with backbone=%s, params=%d", backbone_name, sum(p.numel() for p in model.parameters()))
    return model, processor
