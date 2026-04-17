from __future__ import annotations

import pandas as pd
import pytest

from shared.base_strategy import BaseStrategy
from shared.types import StrategyValidationError


class ExampleStrategy(BaseStrategy):
    slug = "example"
    name = "Example"
    category = "trend"
    default_params = {"threshold": 1}

    def validate_params(self) -> None:
        if self.params["threshold"] < 1:
            raise StrategyValidationError("threshold must be positive")

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["above_open"] = df["close"] > df["open"]
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df["entry_long"] = df["above_open"]
        df["entry_short"] = False
        df["exit_long"] = ~df["above_open"]
        df["exit_short"] = False
        return df


def test_base_strategy_runs_on_copy(ohlcv_df):
    strategy = ExampleStrategy()

    result = strategy.run(ohlcv_df)

    assert "above_open" not in ohlcv_df.columns
    assert "above_open" in result.columns
    assert result["entry_long"].dtype == bool


def test_base_strategy_rejects_missing_columns(ohlcv_df):
    strategy = ExampleStrategy()

    with pytest.raises(StrategyValidationError, match="required OHLCV"):
        strategy.run(ohlcv_df.drop(columns=["volume"]))


def test_base_strategy_rejects_invalid_params():
    with pytest.raises(StrategyValidationError, match="threshold"):
        ExampleStrategy(params={"threshold": 0})

