"""Market data adapters for closed-candle runtime trading."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from logging import Logger

import requests

from .config import MarketConfig
from .models import Candle
from .utils import safe_float, seconds_until_next_candle, utc_now


class BaseMarketDataClient(ABC):
    """Abstraction over the market data source."""

    @abstractmethod
    def load_initial_history(self, limit: int) -> list[Candle]:
        """Load historical closed candles required for warmup."""

    @abstractmethod
    def wait_for_next_closed_candle(self, last_closed_time: datetime | None) -> Candle:
        """Block until a new closed candle is available."""

    @staticmethod
    def update_candle_buffer(buffer: list[Candle], candle: Candle, max_length: int) -> list[Candle]:
        """Append or replace the latest candle in a bounded buffer."""

        if buffer and buffer[-1].close_time == candle.close_time:
            buffer[-1] = candle
        elif not buffer or candle.close_time > buffer[-1].close_time:
            buffer.append(candle)

        if len(buffer) > max_length:
            buffer = buffer[-max_length:]
        return buffer


class PollingBinanceMarketDataClient(BaseMarketDataClient):
    """REST-polling Binance market data client using closed candles only."""

    def __init__(self, config: MarketConfig, logger: Logger) -> None:
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        self.session.trust_env = False

    def load_initial_history(self, limit: int) -> list[Candle]:
        """Load candles in 1000-bar batches, mirroring notebook-style history bootstrapping."""

        all_rows: list[list[object]] = []
        end_time_ms: int | None = None

        while len(all_rows) < limit:
            request_limit = min(1000, limit - len(all_rows))
            params: dict[str, object] = {
                "symbol": self.config.symbol,
                "interval": self.config.timeframe,
                "limit": request_limit,
            }
            if end_time_ms is not None:
                params["endTime"] = end_time_ms - 1

            response = self.session.get(
                self.config.binance_rest_url,
                params=params,
                timeout=self.config.request_timeout_seconds,
            )
            response.raise_for_status()
            rows = response.json()

            if not rows:
                break

            all_rows = rows + all_rows
            end_time_ms = int(rows[0][0])

            if len(rows) < request_limit:
                break

            time.sleep(0.1)

        candles = [self._parse_kline(row) for row in all_rows]
        candles = sorted(candles, key=lambda candle: candle.close_time)

        deduplicated: list[Candle] = []
        seen: set[datetime] = set()
        for candle in candles:
            if candle.close_time in seen:
                continue
            deduplicated.append(candle)
            seen.add(candle.close_time)

        return deduplicated[-limit:]

    def wait_for_next_closed_candle(self, last_closed_time: datetime | None) -> Candle:
        """Poll Binance until a candle with a later close time is observed."""

        while True:
            candle = self._fetch_latest_closed_candle()
            if last_closed_time is None or candle.close_time > last_closed_time:
                return candle

            sleep_seconds = min(
                max(1.0, seconds_until_next_candle(self.config.timeframe) + 0.5),
                self.config.poll_interval_seconds,
            )
            self.logger.debug("No new closed candle yet. Sleeping %.2fs", sleep_seconds)
            time.sleep(sleep_seconds)

    def _fetch_latest_closed_candle(self) -> Candle:
        """Fetch the latest closed candle by taking the latest candle ending before now."""

        response = self.session.get(
            self.config.binance_rest_url,
            params={
                "symbol": self.config.symbol,
                "interval": self.config.timeframe,
                "limit": 3,
            },
            timeout=self.config.request_timeout_seconds,
        )
        response.raise_for_status()

        rows = response.json()
        if not rows:
            raise RuntimeError("Market data request returned no candles.")

        now_ms = int(utc_now().timestamp() * 1000)
        closed_rows = [row for row in rows if int(row[6]) < now_ms]
        if not closed_rows:
            time.sleep(self.config.retry_sleep_seconds)
            return self._fetch_latest_closed_candle()

        return self._parse_kline(closed_rows[-1])

    @staticmethod
    def _parse_kline(row: list[object]) -> Candle:
        """Normalize a raw Binance kline row."""

        return Candle(
            open_time=datetime.fromtimestamp(int(row[0]) / 1000, tz=UTC),
            close_time=datetime.fromtimestamp(int(row[6]) / 1000, tz=UTC),
            open=safe_float(row[1]),
            high=safe_float(row[2]),
            low=safe_float(row[3]),
            close=safe_float(row[4]),
            volume=safe_float(row[5]),
        )
