"""Bollinger Bands."""

from __future__ import annotations

import pandas as pd


def bollinger_bands(
    series: pd.Series, period: int = 20, std_multiplier: float = 2.0
) -> pd.DataFrame:
    """Compute Bollinger middle, upper, and lower bands."""

    if period < 1:
        raise ValueError("period must be greater than or equal to 1")
    if std_multiplier <= 0:
        raise ValueError("std_multiplier must be greater than 0")

    rolling = series.rolling(window=period, min_periods=period)
    middle = rolling.mean()
    std = rolling.std(ddof=0)
    return pd.DataFrame(
        {
            "bollinger_mid": middle,
            "bollinger_upper": middle + std_multiplier * std,
            "bollinger_lower": middle - std_multiplier * std,
        },
        index=series.index,
    )

