"""Structured JSON logging helpers for the trading application."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _serialize_value(value: Any) -> Any:
    """Convert logging values to JSON-serializable representations."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): _serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize_value(item) for item in value]
    return str(value)


class JsonLinesFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "event_type": getattr(record, "event_type", "log"),
        }

        for key, value in record.__dict__.items():
            if key.startswith("_") or key in {
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            }:
                continue
            payload[key] = _serialize_value(value)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def _build_handler(
    handler: logging.Handler,
    level: int,
) -> logging.Handler:
    handler.setLevel(level)
    handler.setFormatter(JsonLinesFormatter())
    return handler


def get_logger(
    name: str,
    *,
    level: str | int = logging.INFO,
    log_file: str | Path | None = None,
    enable_stdout: bool = True,
    enable_file: bool = True,
) -> logging.Logger:
    """Create or reuse an application logger configured for JSON lines."""
    resolved_level = logging.getLevelName(level) if isinstance(level, str) else level
    if isinstance(resolved_level, str):
        resolved_level = logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(resolved_level)
    logger.propagate = False

    if getattr(logger, "_trade360_configured", False):
        return logger

    if enable_stdout:
        logger.addHandler(_build_handler(logging.StreamHandler(), resolved_level))

    if enable_file and log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.addHandler(
            _build_handler(logging.FileHandler(log_path, encoding="utf-8"), resolved_level)
        )

    logger._trade360_configured = True  # type: ignore[attr-defined]
    return logger


@dataclass(slots=True)
class StructuredLogger:
    """Convenience wrapper for logging structured events."""

    logger: logging.Logger
    default_fields: dict[str, Any] = field(default_factory=dict)

    def log(
        self,
        level: int,
        message: str,
        *,
        event_type: str,
        **fields: Any,
    ) -> None:
        payload = {**self.default_fields, **fields}
        self.logger.log(level, message, extra={"event_type": event_type, **payload})

    def info(self, message: str, *, event_type: str, **fields: Any) -> None:
        self.log(logging.INFO, message, event_type=event_type, **fields)

    def warning(self, message: str, *, event_type: str, **fields: Any) -> None:
        self.log(logging.WARNING, message, event_type=event_type, **fields)

    def error(self, message: str, *, event_type: str, **fields: Any) -> None:
        self.log(logging.ERROR, message, event_type=event_type, **fields)
