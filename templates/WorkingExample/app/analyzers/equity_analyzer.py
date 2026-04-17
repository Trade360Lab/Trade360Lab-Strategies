"""Custom analyzer for collecting equity curve observations."""

from __future__ import annotations

from typing import Any

import backtrader as bt


class EquityAnalyzer(bt.Analyzer):
    """Capture equity curve points on every processed bar."""

    def start(self) -> None:
        self._points: list[dict[str, Any]] = []
        self._peak_value = float(self.strategy.broker.getvalue())
        self._realized_pnl = 0.0

    def notify_trade(self, trade: bt.Trade) -> None:
        if trade.isclosed:
            self._realized_pnl += float(getattr(trade, "pnlcomm", 0.0) or 0.0)

    def next(self) -> None:
        close = float(self.strategy.data.close[0])
        cash = float(self.strategy.broker.getcash())
        value = float(self.strategy.broker.getvalue())
        position_size = float(self.strategy.position.size)
        position_price = float(self.strategy.position.price) if position_size else None
        unrealized_pnl = (
            (close - float(self.strategy.position.price)) * position_size
            if position_size
            else 0.0
        )
        self._peak_value = max(self._peak_value, value)
        drawdown_pct = (
            (self._peak_value - value) / self._peak_value * 100.0
            if self._peak_value
            else 0.0
        )

        self._points.append(
            {
                "datetime": self.strategy.datas[0].datetime.datetime(0).isoformat(),
                "cash": round(cash, 8),
                "equity": round(value, 8),
                "close": round(close, 8),
                "position_size": round(position_size, 8),
                "position_price": round(position_price, 8) if position_price is not None else None,
                "unrealized_pnl": round(unrealized_pnl, 8),
                "realized_pnl": round(self._realized_pnl, 8),
                "drawdown_pct": round(drawdown_pct, 8),
            }
        )

    def get_analysis(self) -> list[dict[str, Any]]:
        return self._points
