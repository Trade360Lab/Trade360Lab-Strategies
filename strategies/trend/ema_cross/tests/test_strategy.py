from __future__ import annotations

import pandas as pd
import pytest

from shared.types import REQUIRED_SIGNAL_COLUMNS, StrategyValidationError
from strategies.trend.ema_cross.strategy import EMACrossStrategy


def test_ema_cross_smoke(ohlcv_df):
    result = EMACrossStrategy().run(ohlcv_df)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(ohlcv_df)


def test_ema_cross_schema(ohlcv_df):
    result = EMACrossStrategy().run(ohlcv_df)

    for column in REQUIRED_SIGNAL_COLUMNS:
        assert column in result.columns


def test_ema_cross_is_deterministic(ohlcv_df):
    strategy = EMACrossStrategy()

    first = strategy.run(ohlcv_df)
    second = strategy.run(ohlcv_df)

    pd.testing.assert_frame_equal(first, second)


def test_ema_cross_rejects_invalid_params():
    with pytest.raises(StrategyValidationError, match="smaller"):
        EMACrossStrategy(
            params={"fast_period": 20, "slow_period": 10, "allow_short": True}
        )


def test_ema_cross_has_no_lookahead_dependency(ohlcv_df):
    strategy = EMACrossStrategy()

    truncated = strategy.run(ohlcv_df.iloc[:-5])
    full = strategy.run(ohlcv_df)

    pd.testing.assert_frame_equal(
        truncated[["ema_fast", "ema_slow", *REQUIRED_SIGNAL_COLUMNS]],
        full.iloc[:-5][["ema_fast", "ema_slow", *REQUIRED_SIGNAL_COLUMNS]],
    )
