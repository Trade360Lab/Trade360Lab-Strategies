"""EMA crossover strategy."""

from __future__ import annotations

import pandas as pd

from indicators.trend.ema import ema
from shared.base_strategy import BaseStrategy
from shared.signals import crossover, crossunder
from shared.types import StrategyValidationError


class EMACrossStrategy(BaseStrategy):
    """Trend-following EMA crossover strategy with optional short support."""

    slug = "ema_cross"
    name = "EMA Crossover"
    category = "trend"
    default_params = {
        "fast_period": 12,
        "slow_period": 26,
        "allow_short": True,
    }

    def validate_params(self) -> None:
        fast_period = self.params["fast_period"]
        slow_period = self.params["slow_period"]
        allow_short = self.params["allow_short"]

        if not isinstance(fast_period, int) or fast_period < 1:
            raise StrategyValidationError("fast_period must be an integer >= 1.")
        if not isinstance(slow_period, int) or slow_period < 1:
            raise StrategyValidationError("slow_period must be an integer >= 1.")
        if fast_period >= slow_period:
            raise StrategyValidationError("fast_period must be smaller than slow_period.")
        if not isinstance(allow_short, bool):
            raise StrategyValidationError("allow_short must be a boolean.")

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["ema_fast"] = ema(df["close"], self.params["fast_period"])
        df["ema_slow"] = ema(df["close"], self.params["slow_period"])
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        entry_long = crossover(df["ema_fast"], df["ema_slow"]).fillna(False)
        exit_long = crossunder(df["ema_fast"], df["ema_slow"]).fillna(False)

        df["entry_long"] = entry_long
        df["exit_long"] = exit_long
        df["entry_short"] = False
        df["exit_short"] = False

        if self.params["allow_short"]:
            df["entry_short"] = exit_long
            df["exit_short"] = entry_long

        return df

