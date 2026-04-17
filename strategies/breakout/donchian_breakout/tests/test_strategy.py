from __future__ import annotations

import pandas as pd
import pytest

from shared.types import REQUIRED_SIGNAL_COLUMNS, StrategyValidationError
from strategies.breakout.donchian_breakout.strategy import DonchianBreakoutStrategy


def test_donchian_breakout_smoke(ohlcv_df):
    result = DonchianBreakoutStrategy().run(ohlcv_df)

    assert isinstance(result, pd.DataFrame)
    assert "donchian_upper" in result.columns


def test_donchian_breakout_schema(ohlcv_df):
    result = DonchianBreakoutStrategy().run(ohlcv_df)

    for column in REQUIRED_SIGNAL_COLUMNS:
        assert column in result.columns


def test_donchian_breakout_is_deterministic(ohlcv_df):
    strategy = DonchianBreakoutStrategy()

    first = strategy.run(ohlcv_df)
    second = strategy.run(ohlcv_df)

    pd.testing.assert_frame_equal(first, second)


def test_donchian_breakout_rejects_invalid_params():
    with pytest.raises(StrategyValidationError, match="lookback"):
        DonchianBreakoutStrategy(
            params={"lookback": 1, "exit_lookback": 10, "allow_short": True}
        )


def test_donchian_breakout_has_no_lookahead_dependency(ohlcv_df):
    strategy = DonchianBreakoutStrategy()

    truncated = strategy.run(ohlcv_df.iloc[:-5])
    full = strategy.run(ohlcv_df)

    pd.testing.assert_frame_equal(
        truncated[
            [
                "donchian_upper",
                "donchian_lower",
                "donchian_mid",
                "donchian_exit_upper",
                "donchian_exit_lower",
                "donchian_exit_mid",
                *REQUIRED_SIGNAL_COLUMNS,
            ]
        ],
        full.iloc[:-5][
            [
                "donchian_upper",
                "donchian_lower",
                "donchian_mid",
                "donchian_exit_upper",
                "donchian_exit_lower",
                "donchian_exit_mid",
                *REQUIRED_SIGNAL_COLUMNS,
            ]
        ],
    )
