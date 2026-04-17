"""Relative Strength Index."""

from __future__ import annotations

import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Compute RSI using smoothed average gains and losses."""

    if period < 1:
        raise ValueError("period must be greater than or equal to 1")

    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    average_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    average_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    relative_strength = average_gain / average_loss.replace(0.0, pd.NA)
    return 100 - (100 / (1 + relative_strength))

