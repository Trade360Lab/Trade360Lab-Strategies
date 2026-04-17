from __future__ import annotations

import pandas as pd

from indicators.momentum.rsi import rsi
from indicators.trend.donchian import donchian_channel
from indicators.trend.ema import ema
from indicators.volatility.atr import atr
from indicators.volatility.bollinger import bollinger_bands


def test_ema_returns_series_with_expected_name_and_nan_warmup():
    series = pd.Series([1, 2, 3, 4, 5], dtype=float)
    result = ema(series, period=3)

    assert result.isna().sum() == 2
    assert result.iloc[-1] > result.iloc[-2]


def test_rsi_returns_bounded_values():
    series = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107], dtype=float)
    result = rsi(series, period=3).dropna()

    assert not result.empty
    assert ((result >= 0) & (result <= 100)).all()


def test_bollinger_bands_return_expected_columns():
    series = pd.Series(range(1, 30), dtype=float)
    result = bollinger_bands(series, period=5, std_multiplier=2.0)

    assert list(result.columns) == [
        "bollinger_mid",
        "bollinger_upper",
        "bollinger_lower",
    ]


def test_atr_returns_series_with_same_index(ohlcv_df):
    result = atr(ohlcv_df, period=14)

    assert result.index.equals(ohlcv_df.index)


def test_donchian_channel_returns_expected_columns(ohlcv_df):
    result = donchian_channel(ohlcv_df, lookback=5)

    assert list(result.columns) == [
        "donchian_upper",
        "donchian_lower",
        "donchian_mid",
    ]

