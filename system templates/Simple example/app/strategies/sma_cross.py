import backtrader as bt
from app.strategies.base_strategy import BaseStrategy


class SmaCrossStrategy(BaseStrategy):
    params = (
        ("fast", 20),
        ("slow", 50),
        ("printlog", True),
    )

    def build_indicators(self):
        self.fast_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.p.fast
        )
        self.slow_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.p.slow
        )
        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)

    def long_signal(self):
        return self.crossover[0] > 0

    def short_signal(self):
        return self.crossover[0] < 0

    def exit_signal(self):
        return False

    def signal_reason(self, signal_type: str) -> str | None:
        return (
            f"sma_cross_{signal_type}_fast={self.fast_sma[0]:.4f}_"
            f"slow={self.slow_sma[0]:.4f}"
        )
