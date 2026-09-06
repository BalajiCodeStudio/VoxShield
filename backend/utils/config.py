"""Configuration loader for VoxShield backend."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


_PROJECT_ROOT: Path | None = None


def get_project_root() -> Path:
    """Return the VoxShield project root directory."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is not None:
        return _PROJECT_ROOT
    # Walk up from this file until we find ml/configs/config.yaml
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "ml" / "configs" / "config.yaml").exists():
            _PROJECT_ROOT = parent
            return parent
    # Fallback: assume this file is backend/utils/ and root is 2 levels up
    _PROJECT_ROOT = current.parents[1]
    return _PROJECT_ROOT


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load the project config.yaml.

    Priority: explicit path > VOXSHIELD_CONFIG env var > default location.
    """
    root = get_project_root()
    if config_path is None:
        config_path = os.environ.get(
            "VOXSHIELD_CONFIG",
            str(root / "ml" / "configs" / "config.yaml"),
        )
    path = Path(config_path)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_path(cfg: dict, relative_path: str) -> Path:
    """Resolve a config relative path against the project root."""
    return get_project_root() / relative_path


def ensure_cache_dir(cfg: dict) -> Path:
    """Ensure the cache directory exists and return its path."""
    cache = resolve_path(cfg, cfg["paths"]["cache_dir"])
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path
