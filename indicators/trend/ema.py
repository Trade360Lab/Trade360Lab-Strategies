"""Exponential moving average helpers."""

from __future__ import annotations

import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    """Compute an EMA using pandas' exponentially weighted window."""

    if period < 1:
        raise ValueError("period must be greater than or equal to 1")
    return series.ewm(span=period, adjust=False, min_periods=period).mean()

