"""Donchian channel helpers."""

from __future__ import annotations

import pandas as pd


def donchian_channel(df: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """Compute upper, lower, and midpoint Donchian channel values."""

    if lookback < 1:
        raise ValueError("lookback must be greater than or equal to 1")

    upper = df["high"].rolling(window=lookback, min_periods=lookback).max()
    lower = df["low"].rolling(window=lookback, min_periods=lookback).min()
    midpoint = (upper + lower) / 2.0
    return pd.DataFrame(
        {
            "donchian_upper": upper,
            "donchian_lower": lower,
            "donchian_mid": midpoint,
        },
        index=df.index,
    )
