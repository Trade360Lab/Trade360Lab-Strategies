"""Donchian breakout strategy."""

from __future__ import annotations

import pandas as pd

from indicators.trend.donchian import donchian_channel
from shared.base_strategy import BaseStrategy
from shared.signals import crossover, crossunder
from shared.types import StrategyValidationError


class DonchianBreakoutStrategy(BaseStrategy):
    """Breakout strategy using Donchian channel entries and exits."""

    slug = "donchian_breakout"
    name = "Donchian Breakout"
    category = "breakout"
    default_params = {
        "lookback": 20,
        "exit_lookback": 10,
        "allow_short": True,
    }

    def validate_params(self) -> None:
        lookback = self.params["lookback"]
        exit_lookback = self.params["exit_lookback"]
        allow_short = self.params["allow_short"]

        if not isinstance(lookback, int) or lookback < 2:
            raise StrategyValidationError("lookback must be an integer >= 2.")
        if not isinstance(exit_lookback, int) or exit_lookback < 2:
            raise StrategyValidationError("exit_lookback must be an integer >= 2.")
        if not isinstance(allow_short, bool):
            raise StrategyValidationError("allow_short must be a boolean.")

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        entry_channel = donchian_channel(df, self.params["lookback"])
        exit_channel = donchian_channel(df, self.params["exit_lookback"]).rename(
            columns={
                "donchian_upper": "donchian_exit_upper",
                "donchian_lower": "donchian_exit_lower",
                "donchian_mid": "donchian_exit_mid",
            }
        )
        return df.join(entry_channel).join(exit_channel)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        entry_upper = df["donchian_upper"].shift(1)
        entry_lower = df["donchian_lower"].shift(1)
        exit_mid = df["donchian_exit_mid"].shift(1)

        df["entry_long"] = crossover(df["close"], entry_upper).fillna(False)
        df["exit_long"] = crossunder(df["close"], exit_mid).fillna(False)
        df["entry_short"] = False
        df["exit_short"] = False

        if self.params["allow_short"]:
            df["entry_short"] = crossunder(df["close"], entry_lower).fillna(False)
            df["exit_short"] = crossover(df["close"], exit_mid).fillna(False)

        return df

