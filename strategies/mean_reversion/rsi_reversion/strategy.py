"""RSI mean reversion strategy."""

from __future__ import annotations

import pandas as pd

from indicators.momentum.rsi import rsi
from shared.base_strategy import BaseStrategy
from shared.signals import crossover, crossunder
from shared.types import StrategyValidationError


class RSIReversionStrategy(BaseStrategy):
    """Mean-reversion strategy that reacts to RSI regime reversals."""

    slug = "rsi_reversion"
    name = "RSI Reversion"
    category = "mean_reversion"
    default_params = {
        "rsi_period": 14,
        "oversold": 30.0,
        "overbought": 70.0,
        "exit_mid": 50.0,
        "allow_short": True,
    }

    def validate_params(self) -> None:
        rsi_period = self.params["rsi_period"]
        oversold = self.params["oversold"]
        overbought = self.params["overbought"]
        exit_mid = self.params["exit_mid"]
        allow_short = self.params["allow_short"]

        if not isinstance(rsi_period, int) or rsi_period < 2:
            raise StrategyValidationError("rsi_period must be an integer >= 2.")
        if not all(isinstance(value, (int, float)) for value in (oversold, overbought, exit_mid)):
            raise StrategyValidationError("RSI threshold parameters must be numeric.")
        if not 0 <= oversold < exit_mid < overbought <= 100:
            raise StrategyValidationError(
                "Expected 0 <= oversold < exit_mid < overbought <= 100."
            )
        if not isinstance(allow_short, bool):
            raise StrategyValidationError("allow_short must be a boolean.")

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["rsi"] = rsi(df["close"], self.params["rsi_period"])
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        oversold_line = pd.Series(self.params["oversold"], index=df.index)
        overbought_line = pd.Series(self.params["overbought"], index=df.index)
        exit_mid_line = pd.Series(self.params["exit_mid"], index=df.index)

        entry_long = crossover(df["rsi"], oversold_line).fillna(False)
        exit_long = (
            crossover(df["rsi"], exit_mid_line) | crossover(df["rsi"], overbought_line)
        ).fillna(False)

        df["entry_long"] = entry_long
        df["exit_long"] = exit_long
        df["entry_short"] = False
        df["exit_short"] = False

        if self.params["allow_short"]:
            df["entry_short"] = crossunder(df["rsi"], overbought_line).fillna(False)
            df["exit_short"] = (
                crossunder(df["rsi"], exit_mid_line)
                | crossunder(df["rsi"], oversold_line)
            ).fillna(False)

        return df

