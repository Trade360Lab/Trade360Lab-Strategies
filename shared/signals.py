"""Reusable helpers for common signal-generation patterns."""

from __future__ import annotations

import numpy as np
import pandas as pd


def crossover(series_a: pd.Series, series_b: pd.Series) -> pd.Series:
    """Return ``True`` when ``series_a`` crosses above ``series_b`` on the bar."""

    previous_a = series_a.shift(1)
    previous_b = series_b.shift(1)
    return (series_a > series_b) & (previous_a <= previous_b)


def crossunder(series_a: pd.Series, series_b: pd.Series) -> pd.Series:
    """Return ``True`` when ``series_a`` crosses below ``series_b`` on the bar."""

    previous_a = series_a.shift(1)
    previous_b = series_b.shift(1)
    return (series_a < series_b) & (previous_a >= previous_b)


def rising(series: pd.Series, window: int = 1) -> pd.Series:
    """Return ``True`` when the series is rising relative to ``window`` bars ago."""

    if window < 1:
        raise ValueError("window must be greater than or equal to 1")
    return series > series.shift(window)


def falling(series: pd.Series, window: int = 1) -> pd.Series:
    """Return ``True`` when the series is falling relative to ``window`` bars ago."""

    if window < 1:
        raise ValueError("window must be greater than or equal to 1")
    return series < series.shift(window)


def bars_since(condition: pd.Series) -> pd.Series:
    """Count elapsed bars since the most recent ``True`` value."""

    normalized = condition.fillna(False).astype(bool)
    result = np.full(len(normalized), np.nan)
    last_true_index = None

    for index, is_true in enumerate(normalized):
        if is_true:
            last_true_index = index
            result[index] = 0
        elif last_true_index is not None:
            result[index] = index - last_true_index

    return pd.Series(result, index=condition.index)


def debounce_signal(condition: pd.Series, cooloff_bars: int = 0) -> pd.Series:
    """Suppress repeated ``True`` values for a configurable number of bars."""

    if cooloff_bars < 0:
        raise ValueError("cooloff_bars must be greater than or equal to 0")

    normalized = condition.fillna(False).astype(bool)
    result: list[bool] = []
    remaining_cooloff = 0

    for is_true in normalized:
        if is_true and remaining_cooloff == 0:
            result.append(True)
            remaining_cooloff = cooloff_bars
            continue

        result.append(False)
        if remaining_cooloff > 0:
            remaining_cooloff -= 1

    return pd.Series(result, index=condition.index, dtype=bool)
