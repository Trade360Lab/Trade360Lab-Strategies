"""Utility helpers for logging, parsing and time handling."""

from __future__ import annotations

import logging
import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from pathlib import Path


def setup_logger(name: str, log_level: str, logs_dir: Path) -> logging.Logger:
    """Build a stdout + file logger."""

    logs_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_name = f"{name.strip().lower().replace(' ', '_')}.log"
    file_handler = logging.FileHandler(logs_dir / file_name, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger


def safe_float(value: object, default: float = 0.0) -> float:
    """Convert a value to finite float with fallback."""

    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)

    if not math.isfinite(result):
        return float(default)
    return result


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not exist."""

    path.mkdir(parents=True, exist_ok=True)
    return path


def round_to_step(value: float, step: float) -> float:
    """Round a numeric value down to exchange-like step precision."""

    if step <= 0:
        return value
    decimal_value = Decimal(str(value))
    decimal_step = Decimal(str(step))
    steps = (decimal_value / decimal_step).to_integral_value(rounding=ROUND_DOWN)
    return float(steps * decimal_step)


def round_quantity(quantity: float, step: float, min_quantity: float) -> float:
    """Round quantity down and enforce minimum size."""

    rounded = round_to_step(quantity, step)
    return rounded if rounded >= min_quantity else 0.0


def round_price(price: float, step: float) -> float:
    """Round price down to the configured tick size."""

    return round_to_step(price, step)


def utc_now() -> datetime:
    """Return timezone-aware UTC now."""

    return datetime.now(tz=UTC)


def timeframe_to_timedelta(timeframe: str) -> timedelta:
    """Convert a Binance-like timeframe string to timedelta."""

    unit = timeframe[-1].lower()
    value = int(timeframe[:-1])

    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)
    raise ValueError(f"Unsupported timeframe: {timeframe}")


def seconds_until_next_candle(timeframe: str, now: datetime | None = None) -> float:
    """Return seconds until the next candle close for the given timeframe."""

    current_time = now or utc_now()
    delta = timeframe_to_timedelta(timeframe)
    epoch_seconds = current_time.timestamp()
    candle_seconds = delta.total_seconds()
    next_close = math.floor(epoch_seconds / candle_seconds) * candle_seconds + candle_seconds
    return max(0.0, next_close - epoch_seconds)
