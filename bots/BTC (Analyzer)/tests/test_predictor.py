from pathlib import Path

import pandas as pd
import pytest

from predictor import build_features, predict_latest_forecast


def test_feature_build_minimal() -> None:
    index = pd.date_range("2026-01-01", periods=80, freq="h", tz="UTC")
    close_values = [100 + (i * 0.5) + ((-1) ** i) * 2 for i in range(80)]
    close = pd.Series(close_values, index=index, dtype=float)
    df = pd.DataFrame(
        {
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=index,
    )

    features = build_features(df)

    assert not features.empty
    assert "rsi_14" in features.columns
    assert "hour" in features.columns


def test_missing_artifacts_raises(tmp_path: Path) -> None:
    index = pd.date_range("2026-01-01", periods=80, freq="h", tz="UTC")
    df = pd.DataFrame(
        {
            "open": range(100, 180),
            "high": range(101, 181),
            "low": range(99, 179),
            "close": range(100, 180),
            "volume": [1000.0] * 80,
        },
        index=index,
    )

    with pytest.raises(FileNotFoundError):
        predict_latest_forecast(df=df, artifacts_dir=tmp_path)
