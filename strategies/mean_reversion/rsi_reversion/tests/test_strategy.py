from __future__ import annotations

import pandas as pd
import pytest

from shared.types import REQUIRED_SIGNAL_COLUMNS, StrategyValidationError
from strategies.mean_reversion.rsi_reversion.strategy import RSIReversionStrategy


def test_rsi_reversion_smoke(ohlcv_df):
    result = RSIReversionStrategy().run(ohlcv_df)

    assert isinstance(result, pd.DataFrame)
    assert "rsi" in result.columns


def test_rsi_reversion_schema(ohlcv_df):
    result = RSIReversionStrategy().run(ohlcv_df)

    for column in REQUIRED_SIGNAL_COLUMNS:
        assert column in result.columns


def test_rsi_reversion_is_deterministic(ohlcv_df):
    strategy = RSIReversionStrategy()

    first = strategy.run(ohlcv_df)
    second = strategy.run(ohlcv_df)

    pd.testing.assert_frame_equal(first, second)


def test_rsi_reversion_rejects_invalid_params():
    with pytest.raises(StrategyValidationError, match="oversold < exit_mid < overbought"):
        RSIReversionStrategy(
            params={
                "rsi_period": 14,
                "oversold": 55.0,
                "overbought": 70.0,
                "exit_mid": 50.0,
                "allow_short": True,
            }
        )


def test_rsi_reversion_has_no_lookahead_dependency(ohlcv_df):
    strategy = RSIReversionStrategy()

    truncated = strategy.run(ohlcv_df.iloc[:-5])
    full = strategy.run(ohlcv_df)

    pd.testing.assert_frame_equal(
        truncated[["rsi", *REQUIRED_SIGNAL_COLUMNS]],
        full.iloc[:-5][["rsi", *REQUIRED_SIGNAL_COLUMNS]],
    )
