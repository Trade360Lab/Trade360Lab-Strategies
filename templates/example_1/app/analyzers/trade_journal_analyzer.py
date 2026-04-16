"""Custom analyzer for extracting a trade journal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import backtrader as bt


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_iso(dt_value: float | datetime | None) -> str | None:
    if dt_value in (None, 0):
        return None
    if isinstance(dt_value, datetime):
        return dt_value.isoformat()
    try:
        return bt.num2date(dt_value).isoformat()
    except (TypeError, ValueError):
        return None


@dataclass(slots=True)
class _OpenTradeSnapshot:
    trade_id: int
    direction: str
    entry_dt: str | None
    entry_price: float | None
    size: float | None
    signal_reason: str | None
    mae: float = 0.0
    mfe: float = 0.0


class TradeJournalAnalyzer(bt.Analyzer):
    """Collect a serializable trade journal."""

    def start(self) -> None:
        self._open_trades: dict[int, _OpenTradeSnapshot] = {}
        self._trades: list[dict[str, Any]] = []
        self._trade_counter = 0

    def notify_trade(self, trade: bt.Trade) -> None:
        trade_id = int(getattr(trade, "ref", 0) or 0)
        if trade_id == 0:
            self._trade_counter += 1
            trade_id = self._trade_counter

        if trade.justopened:
            self._open_trades[trade_id] = _OpenTradeSnapshot(
                trade_id=trade_id,
                direction="long" if getattr(trade, "long", True) else "short",
                entry_dt=_to_iso(getattr(trade, "dtopen", None)),
                entry_price=_safe_float(getattr(trade, "price", None)),
                size=_safe_float(getattr(trade, "size", None)),
                signal_reason=getattr(self.strategy, "_last_signal_reason", None),
            )
            return

        if not trade.isclosed:
            return

        snapshot = self._open_trades.pop(
            trade_id,
            _OpenTradeSnapshot(
                trade_id=trade_id,
                direction="long" if getattr(trade, "long", True) else "short",
                entry_dt=_to_iso(getattr(trade, "dtopen", None)),
                entry_price=_safe_float(getattr(trade, "price", None)),
                size=_safe_float(getattr(trade, "size", None)),
                signal_reason=None,
            ),
        )
        pnl = _safe_float(getattr(trade, "pnl", None))
        pnl_net = _safe_float(getattr(trade, "pnlcomm", None))
        commission = (
            None
            if pnl is None or pnl_net is None
            else round(float(pnl - pnl_net), 8)
        )

        self._trades.append(
            {
                "trade_id": snapshot.trade_id,
                "direction": snapshot.direction,
                "entry_dt": snapshot.entry_dt,
                "exit_dt": _to_iso(getattr(trade, "dtclose", None)),
                "entry_price": snapshot.entry_price,
                "exit_price": _safe_float(self.strategy.data.close[0]),
                "size": snapshot.size,
                "pnl": pnl,
                "pnl_net": pnl_net,
                "commission": commission,
                "bars_held": int(getattr(trade, "barlen", 0) or 0),
                "mae": round(snapshot.mae, 8) if snapshot.mae else 0.0,
                "mfe": round(snapshot.mfe, 8) if snapshot.mfe else 0.0,
                "exit_reason": getattr(self.strategy, "_last_exit_reason", None),
                "signal_reason": snapshot.signal_reason,
            }
        )

    def next(self) -> None:
        low = _safe_float(self.strategy.data.low[0])
        high = _safe_float(self.strategy.data.high[0])
        if low is None or high is None:
            return

        for snapshot in self._open_trades.values():
            if snapshot.entry_price is None:
                continue
            if snapshot.direction == "long":
                snapshot.mae = min(snapshot.mae, low - snapshot.entry_price)
                snapshot.mfe = max(snapshot.mfe, high - snapshot.entry_price)
                continue

            snapshot.mae = min(snapshot.mae, snapshot.entry_price - high)
            snapshot.mfe = max(snapshot.mfe, snapshot.entry_price - low)

    def get_analysis(self) -> dict[str, list[dict[str, Any]]]:
        return {"trades": self._trades}
