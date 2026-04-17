"""Validation helpers for market data inputs and strategy outputs."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype

from shared.types import (
    REQUIRED_OHLCV_COLUMNS,
    REQUIRED_SIGNAL_COLUMNS,
    StrategyValidationError,
)

BOOLEAN_LIKE_VALUES = {0, 1}


def _missing_columns(df: pd.DataFrame, columns: Iterable[str]) -> list[str]:
    return [column for column in columns if column not in df.columns]


def validate_ohlcv_columns(df: pd.DataFrame) -> None:
    """Ensure the dataframe exposes the standard OHLCV column set."""

    missing = _missing_columns(df, REQUIRED_OHLCV_COLUMNS)
    if missing:
        raise StrategyValidationError(
            "Strategy input is missing required OHLCV columns: " + ", ".join(missing)
        )


def validate_dataframe_not_empty(df: pd.DataFrame) -> None:
    """Reject empty inputs early."""

    if df.empty:
        raise StrategyValidationError("Strategy input DataFrame must not be empty.")


def validate_sorted_index_or_timestamp(df: pd.DataFrame) -> None:
    """Require either a monotonic datetime index or a sorted timestamp column."""

    if "timestamp" in df.columns:
        timestamp = df["timestamp"]
        if not is_datetime64_any_dtype(timestamp):
            raise StrategyValidationError(
                "Strategy input column 'timestamp' must use a datetime dtype."
            )
        if not timestamp.is_monotonic_increasing:
            raise StrategyValidationError(
                "Strategy input column 'timestamp' must be sorted ascending."
            )
        return

    if not is_datetime64_any_dtype(df.index):
        raise StrategyValidationError(
            "Strategy input must have a datetime index or a 'timestamp' column."
        )
    if not df.index.is_monotonic_increasing:
        raise StrategyValidationError("Strategy input index must be sorted ascending.")


def validate_no_duplicate_timestamps(df: pd.DataFrame) -> None:
    """Reject duplicate timestamps when a timestamp source is available."""

    if "timestamp" in df.columns and df["timestamp"].duplicated().any():
        raise StrategyValidationError(
            "Strategy input column 'timestamp' must not contain duplicates."
        )
    if is_datetime64_any_dtype(df.index) and df.index.duplicated().any():
        raise StrategyValidationError(
            "Strategy input index must not contain duplicates."
        )


def validate_strategy_output(df: pd.DataFrame) -> None:
    """Validate the standard signal columns and normalize them to booleans."""

    missing = _missing_columns(df, REQUIRED_SIGNAL_COLUMNS)
    if missing:
        raise StrategyValidationError(
            "Strategy output is missing required signal columns: " + ", ".join(missing)
        )

    for column in REQUIRED_SIGNAL_COLUMNS:
        series = df[column]
        if is_bool_dtype(series):
            continue

        non_null_values = set(series.dropna().unique().tolist())
        if not non_null_values.issubset(BOOLEAN_LIKE_VALUES):
            raise StrategyValidationError(
                f"Strategy output column '{column}' must be boolean or boolean-like."
            )
        df[column] = series.fillna(False).astype(bool)
