"""Structured logging for VoxShield backend."""
from __future__ import annotations

import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Any


class StructuredFormatter(logging.Formatter):
    """JSON-formatted log records."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, default=str)


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure structured logging for the application."""
    logger = logging.getLogger("voxshield")
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    return logger


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())[:12]


def log_prediction(
    logger: logging.Logger,
    *,
    request_id: str,
    processing_time_ms: float,
    audio_duration_s: float | None,
    prediction: str,
    confidence: float,
    model_version: str | None = None,
) -> None:
    """Log a prediction event with structured data."""
    logger.info(
        "Prediction completed",
        extra={
            "extra_data": {
                "request_id": request_id,
                "processing_time_ms": round(processing_time_ms, 1),
                "audio_duration_s": round(audio_duration_s, 2) if audio_duration_s else None,
                "prediction": prediction,
                "confidence": round(confidence, 4),
                "model_version": model_version,
            }
        },
    )
