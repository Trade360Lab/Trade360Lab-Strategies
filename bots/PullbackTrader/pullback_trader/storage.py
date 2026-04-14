"""Persistent storage for state, signals and trades."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import AppConfig, StorageConfig
from .models import BotState, OrderResult, PositionState, Signal
from .utils import ensure_directory


def load_state(storage_config: StorageConfig, app_config: AppConfig) -> BotState:
    """Load local bot state from JSON or create a default one."""

    _ensure_storage(storage_config)
    if not storage_config.state_file.exists():
        return BotState(
            symbol=app_config.market.symbol,
            timeframe=app_config.market.timeframe,
            paper_mode=app_config.execution.paper_mode,
            available_cash=app_config.execution.initial_cash,
            kill_switch=app_config.kill_switch,
        )

    raw = json.loads(storage_config.state_file.read_text(encoding="utf-8"))
    position = _position_from_dict(raw.get("position"))

    return BotState(
        symbol=raw.get("symbol", app_config.market.symbol),
        timeframe=raw.get("timeframe", app_config.market.timeframe),
        paper_mode=bool(raw.get("paper_mode", app_config.execution.paper_mode)),
        available_cash=float(raw.get("available_cash", app_config.execution.initial_cash)),
        last_processed_candle_time=_parse_datetime(raw.get("last_processed_candle_time")),
        last_signal_time=_parse_datetime(raw.get("last_signal_time")),
        last_order_time=_parse_datetime(raw.get("last_order_time")),
        last_sync_time=_parse_datetime(raw.get("last_sync_time")),
        position=position,
        kill_switch=bool(raw.get("kill_switch", app_config.kill_switch)),
        recovery_required=bool(raw.get("recovery_required", False)),
        last_error=raw.get("last_error"),
        version=int(raw.get("version", 1)),
    )


def save_state(storage_config: StorageConfig, state: BotState) -> None:
    """Persist bot state to JSON."""

    _ensure_storage(storage_config)
    payload = _serialize(state)
    storage_config.state_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append_signal(storage_config: StorageConfig, signal: Signal) -> None:
    """Append a signal snapshot into CSV."""

    row = {
        "timestamp": signal.timestamp.isoformat(),
        "symbol": signal.symbol,
        "timeframe": signal.timeframe,
        "strategy_name": signal.strategy_name,
        "action": signal.action,
        "side": signal.side,
        "reason": signal.reason,
        "entry_price": signal.entry_price,
        "stop_price": signal.stop_price,
        "take_price": signal.take_price,
        "exit_price": signal.exit_price,
        "quantity": signal.quantity,
        "metadata": json.dumps(signal.metadata, ensure_ascii=False, default=str),
    }
    _append_csv(storage_config.signals_file, row)


def append_trade(storage_config: StorageConfig, order_result: OrderResult) -> None:
    """Append a trade execution row into CSV."""

    row = {
        "timestamp": order_result.timestamp.isoformat(),
        "action": order_result.action,
        "symbol": order_result.symbol,
        "side": order_result.side,
        "status": order_result.status,
        "quantity": order_result.quantity,
        "requested_price": order_result.requested_price,
        "filled_price": order_result.filled_price,
        "reason": order_result.reason,
        "realized_pnl": order_result.realized_pnl,
        "order_id": order_result.order_id,
        "raw": json.dumps(order_result.raw, ensure_ascii=False, default=str),
    }
    _append_csv(storage_config.trades_file, row)


def _ensure_storage(storage_config: StorageConfig) -> None:
    ensure_directory(storage_config.data_path)
    ensure_directory(storage_config.logs_path)
    ensure_directory(storage_config.state_path)


def _append_csv(path: Path, row: dict[str, Any]) -> None:
    ensure_directory(path.parent)
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _position_from_dict(data: dict[str, Any] | None) -> PositionState | None:
    if not data:
        return None
    return PositionState(
        symbol=data["symbol"],
        side=data["side"],
        quantity=float(data["quantity"]),
        entry_price=float(data["entry_price"]),
        entry_time=datetime.fromisoformat(data["entry_time"]),
        stop_price=float(data["stop_price"]),
        take_price=float(data["take_price"]),
        strategy_name=data["strategy_name"],
        entry_reason=data["entry_reason"],
        bars_held=int(data.get("bars_held", 0)),
        exchange_position_id=data.get("exchange_position_id"),
        realized_pnl=float(data.get("realized_pnl", 0.0)),
        last_update_time=_parse_datetime(data.get("last_update_time")),
    )


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value
