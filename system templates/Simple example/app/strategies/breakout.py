"""Simple breakout strategy example."""

from __future__ import annotations

import backtrader as bt

from app.strategies.base_strategy import BaseStrategy


class BreakoutStrategy(BaseStrategy):
    """Go long on breakout above the rolling high and exit on rolling low."""

    params = (
        ("period", 20),
        ("printlog", True),
    )

    def build_indicators(self):
        self.highest_high = bt.indicators.Highest(
            self.data.high(-1), period=self.p.period
        )
        self.lowest_low = bt.indicators.Lowest(
            self.data.low(-1), period=self.p.period
        )

    def long_signal(self):
        return len(self) >= self.p.period and self.data.close[0] > self.highest_high[0]

    def short_signal(self):
        return False

    def exit_signal(self):
        return (
            len(self) >= self.p.period
            and self.position.size > 0
            and self.data.close[0] < self.lowest_low[0]
        )

    def signal_reason(self, signal_type: str) -> str | None:
        return f"breakout_{signal_type}_{self.p.period}"
