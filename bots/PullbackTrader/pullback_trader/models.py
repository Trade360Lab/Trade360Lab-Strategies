"""Shared runtime models for PullbackTrader."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


SignalAction = Literal["hold", "entry", "exit"]


@dataclass(slots=True)
class Candle:
    """Normalized OHLCV candle."""

    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(slots=True)
class Signal:
    """Strategy output for a closed candle."""

    action: SignalAction
    symbol: str
    timeframe: str
    strategy_name: str
    timestamp: datetime
    side: str = "long"
    reason: str = "no_action"
    entry_price: float | None = None
    stop_price: float | None = None
    take_price: float | None = None
    exit_price: float | None = None
    quantity: float | None = None
    risk_per_unit: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_actionable(self) -> bool:
        return self.action in {"entry", "exit"}


@dataclass(slots=True)
class PositionState:
    """Current long position state."""

    symbol: str
    side: str
    quantity: float
    entry_price: float
    entry_time: datetime
    stop_price: float
    take_price: float
    strategy_name: str
    entry_reason: str
    bars_held: int = 0
    exchange_position_id: str | None = None
    realized_pnl: float = 0.0
    last_update_time: datetime | None = None


@dataclass(slots=True)
class OrderRequest:
    """Order request passed into execution clients."""

    symbol: str
    side: str
    quantity: float
    order_type: str
    reduce_only: bool
    signal_time: datetime
    intended_price: float | None = None
    stop_price: float | None = None
    take_price: float | None = None
    reason: str = ""


@dataclass(slots=True)
class OrderResult:
    """Execution result returned by execution clients."""

    accepted: bool
    status: str
    action: str
    symbol: str
    side: str
    quantity: float
    requested_price: float | None
    filled_price: float | None
    reason: str
    timestamp: datetime
    order_id: str | None = None
    realized_pnl: float = 0.0
    position: PositionState | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BotState:
    """Persistent local bot state."""

    symbol: str
    timeframe: str
    paper_mode: bool
    available_cash: float
    last_processed_candle_time: datetime | None = None
    last_signal_time: datetime | None = None
    last_order_time: datetime | None = None
    last_sync_time: datetime | None = None
    position: PositionState | None = None
    kill_switch: bool = False
    recovery_required: bool = False
    last_error: str | None = None
    version: int = 1
