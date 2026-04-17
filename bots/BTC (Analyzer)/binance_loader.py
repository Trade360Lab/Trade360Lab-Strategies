from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd
import requests


LOGGER = logging.getLogger(__name__)
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
DEFAULT_PER_REQUEST = 1000
MAX_RETRIES = 3
BACKOFF_SECONDS = 1.5


class BinanceLoaderError(RuntimeError):
    pass


def _request_klines(
    session: requests.Session,
    params: dict[str, Any],
    timeout_seconds: int,
) -> list[list[Any]]:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(BINANCE_KLINES_URL, params=params, timeout=timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise BinanceLoaderError("Unexpected Binance response format for klines endpoint.")
            return payload
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            LOGGER.warning(
                "Binance request failed for %s %s on attempt %s/%s: %s",
                params.get("symbol"),
                params.get("interval"),
                attempt,
                MAX_RETRIES,
                exc,
            )
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_SECONDS * attempt)
    raise BinanceLoaderError(f"Failed to fetch klines from Binance after {MAX_RETRIES} attempts.") from last_error


def load_binance_klines(
    symbol: str = "BTCUSDT",
    interval: str = "5m",
    limit_total: int = 10_000,
    timeout_seconds: int = 20,
    use_closed_candle_only: bool = True,
) -> pd.DataFrame:
    if limit_total <= 0:
        raise ValueError("limit_total must be positive.")

    all_klines: list[list[Any]] = []
    end_time: int | None = None
    session = requests.Session()
    session.trust_env = False

    while len(all_klines) < limit_total:
        params: dict[str, Any] = {
            "symbol": symbol,
            "interval": interval,
            "limit": min(DEFAULT_PER_REQUEST, limit_total - len(all_klines)),
        }
        if end_time is not None:
            params["endTime"] = end_time - 1

        klines = _request_klines(session=session, params=params, timeout_seconds=timeout_seconds)
        if not klines:
            break

        all_klines = klines + all_klines
        end_time = int(klines[0][0])
        time.sleep(0.1)

    if not all_klines:
        raise BinanceLoaderError(f"Binance returned no klines for {symbol} {interval}.")

    df_binance = pd.DataFrame(
        all_klines[-limit_total:],
        columns=[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "qav",
            "num_trades",
            "taker_base",
            "taker_quote",
            "ignore",
        ],
    )

    numeric_cols = ["open", "high", "low", "close", "volume"]
    for col in numeric_cols:
        df_binance[col] = pd.to_numeric(df_binance[col], errors="coerce")

    df_binance["datetime"] = pd.to_datetime(df_binance["open_time"], unit="ms", utc=True)
    df_binance = df_binance[["datetime", "open", "high", "low", "close", "volume"]]
    df_binance = df_binance.sort_values("datetime").drop_duplicates(subset=["datetime"], keep="last")
    df_binance = df_binance.set_index("datetime")

    if use_closed_candle_only and len(df_binance) > 1:
        df_binance = df_binance.iloc[:-1]

    return validate_ohlcv(df_binance)


def validate_ohlcv(df: pd.DataFrame, expected_freq: str | None = None) -> pd.DataFrame:
    required_columns = ["open", "high", "low", "close", "volume"]
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"OHLCV data is missing required columns: {', '.join(missing_columns)}")
    if df.empty:
        raise ValueError("OHLCV data is empty.")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("OHLCV index must be a DatetimeIndex.")

    validated = df.sort_index().copy()
    if not validated.index.is_monotonic_increasing:
        raise ValueError("OHLCV index must be sorted ascending.")
    if validated.index.has_duplicates:
        raise ValueError("OHLCV index contains duplicate timestamps.")
    if validated[required_columns].isnull().any().any():
        raise ValueError("OHLCV data contains null values.")

    for column in required_columns:
        validated[column] = pd.to_numeric(validated[column], errors="raise")

    invalid_rows = (
        (validated["high"] < validated["low"])
        | (validated["high"] < validated[["open", "close"]].max(axis=1))
        | (validated["low"] > validated[["open", "close"]].min(axis=1))
        | (validated["volume"] < 0)
    )
    if invalid_rows.any():
        raise ValueError("OHLCV data contains invalid candle relationships.")

    if expected_freq:
        expected_delta = pd.to_timedelta(expected_freq)
        deltas = validated.index.to_series().diff().dropna()
        if not deltas.empty and (deltas != expected_delta).any():
            raise ValueError(f"OHLCV data has gaps or irregular spacing. Expected frequency: {expected_freq}")

    return validated
