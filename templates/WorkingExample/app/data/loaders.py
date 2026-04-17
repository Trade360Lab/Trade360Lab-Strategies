"""Data loading helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import backtrader as bt


def load_csv_to_bt(data_path: str) -> bt.feeds.PandasData:
    """Load OHLCV CSV data into a Backtrader data feed."""
    csv_path = Path(data_path)
    df = pd.read_csv(csv_path)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df.set_index("datetime", inplace=True)

    # ожидаемые колонки: open, high, low, close, volume
    return bt.feeds.PandasData(dataname=df, name=csv_path.stem)
