"""Reusable OHLCV fixtures for tests."""

from __future__ import annotations

import numpy as np
import pandas as pd


def make_ohlcv_fixture(length: int = 120) -> pd.DataFrame:
    """Build a deterministic OHLCV dataframe with a datetime index."""

    index = pd.date_range("2024-01-01", periods=length, freq="h", tz="UTC")
    base = np.linspace(100.0, 140.0, num=length)
    oscillation = np.sin(np.linspace(0, 8 * np.pi, num=length)) * 4.0
    close = base + oscillation

    df = pd.DataFrame(
        {
            "open": close - 0.4,
            "high": close + 1.2,
            "low": close - 1.2,
            "close": close,
            "volume": np.linspace(1000.0, 2000.0, num=length),
        },
        index=index,
    )
    return df

