"""Structured trading event logging helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.logging.logger import StructuredLogger


def _normalize_datetime(value: datetime | str | None) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


@dataclass(slots=True)
class EventLogger:
    """Emit trading lifecycle events as structured JSON logs."""

    logger: StructuredLogger
    common_fields: dict[str, Any] = field(default_factory=dict)

    def _emit(
        self,
        event_type: str,
        message: str,
        *,
        level: int = logging.INFO,
        **fields: Any,
    ) -> None:
        payload = {**self.common_fields, **fields}
        for key in (
            "datetime",
            "entry_dt",
            "exit_dt",
        ):
            if key in payload:
                payload[key] = _normalize_datetime(payload[key])
        self.logger.log(level, message, event_type=event_type, **payload)

    def log_bar(self, **fields: Any) -> None:
        self._emit("bar", "Bar processed", **fields)

    def log_signal(self, **fields: Any) -> None:
        self._emit("signal", "Trading signal emitted", **fields)

    def log_order(self, **fields: Any) -> None:
        self._emit("order", "Order status updated", **fields)

    def log_trade(self, **fields: Any) -> None:
        self._emit("trade", "Trade closed", **fields)

    def log_error(self, **fields: Any) -> None:
        self._emit("error", "Strategy error", level=logging.ERROR, **fields)

    def log_run_summary(self, **fields: Any) -> None:
        self._emit("run_summary", "Backtest finished", **fields)
