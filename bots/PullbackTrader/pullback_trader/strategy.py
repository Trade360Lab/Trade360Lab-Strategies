"""Notebook-equivalent Trend + Pullback strategy logic."""

from __future__ import annotations

from logging import Logger

from .config import StrategyConfig
from .models import Candle, PositionState, Signal


def _sma(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if period <= 0 or len(values) < period:
        return result

    rolling_sum = sum(values[:period])
    result[period - 1] = rolling_sum / period

    for index in range(period, len(values)):
        rolling_sum += values[index] - values[index - period]
        result[index] = rolling_sum / period

    return result


def _ema(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if period <= 0 or len(values) < period:
        return result

    seed = sum(values[:period]) / period
    result[period - 1] = seed
    multiplier = 2.0 / (period + 1)
    previous = seed

    for index in range(period, len(values)):
        previous = (values[index] - previous) * multiplier + previous
        result[index] = previous

    return result


def _atr_wilder(candles: list[Candle], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(candles)
    if period <= 0 or len(candles) < period:
        return result

    true_ranges: list[float] = []
    previous_close: float | None = None
    for candle in candles:
        if previous_close is None:
            tr = candle.high - candle.low
        else:
            tr = max(
                candle.high - candle.low,
                abs(candle.high - previous_close),
                abs(candle.low - previous_close),
            )
        true_ranges.append(tr)
        previous_close = candle.close

    seed = sum(true_ranges[:period]) / period
    result[period - 1] = seed
    previous_atr = seed

    for index in range(period, len(true_ranges)):
        previous_atr = ((previous_atr * (period - 1)) + true_ranges[index]) / period
        result[index] = previous_atr

    return result


class TrendPullbackStrategy:
    """Real-time port of the notebook BTC Trend + Pullback logic."""

    def __init__(self, config: StrategyConfig, symbol: str, timeframe: str, logger: Logger) -> None:
        self.config = config
        self.symbol = symbol
        self.timeframe = timeframe
        self.logger = logger

    def evaluate(self, candles: list[Candle], position: PositionState | None) -> Signal:
        """Evaluate the latest closed candle and emit a structured signal."""

        latest = candles[-1]
        if len(candles) < self.config.warmup_bars:
            return Signal(
                action="hold",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="TrendPullback",
                timestamp=latest.close_time,
                reason="warmup",
                metadata={"required_bars": self.config.warmup_bars, "available_bars": len(candles)},
            )

        closes = [candle.close for candle in candles]
        highs = [candle.high for candle in candles]
        lows = [candle.low for candle in candles]
        volumes = [candle.volume for candle in candles]

        ema_fast_values = _ema(closes, self.config.ema_fast)
        ema_slow_values = _ema(closes, self.config.ema_slow)
        atr_values = _atr_wilder(candles, self.config.atr_period)
        volume_sma_values = _sma(volumes, self.config.volume_window)

        ema_fast = ema_fast_values[-1]
        ema_slow = ema_slow_values[-1]
        atr = atr_values[-1]
        volume_sma = volume_sma_values[-1]
        ema_slow_past = ema_slow_values[-1 - self.config.slope_lookback]

        prior_high = self._highest_excluding_current(highs, self.config.swing_window)
        prior_low = self._lowest_excluding_current(lows, self.config.swing_window)
        micro_window = max(3, self.config.swing_window // 2)
        micro_high = self._highest_excluding_current(highs, micro_window)

        if None in {ema_fast, ema_slow, atr, volume_sma, ema_slow_past, prior_high, prior_low, micro_high}:
            return Signal(
                action="hold",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="TrendPullback",
                timestamp=latest.close_time,
                reason="indicator_unavailable",
            )

        latest_close = latest.close
        ema_slow_slope = float(ema_slow - ema_slow_past)
        atr_pct = float(atr / latest_close) if latest_close > 0 else 0.0
        volume_ratio = float(latest.volume / volume_sma) if volume_sma and volume_sma > 0 else 0.0
        pullback_pct = float((prior_high - latest_close) / prior_high) if prior_high > 0 else 0.0

        diagnostics = {
            "close": latest_close,
            "ema_fast": ema_fast,
            "ema_slow": ema_slow,
            "ema_slow_slope": ema_slow_slope,
            "atr": atr,
            "atr_pct": atr_pct,
            "volume_ratio": volume_ratio,
            "pullback_pct": pullback_pct,
            "recent_low": prior_low,
            "micro_high": micro_high,
        }

        if position is not None:
            return self._evaluate_exit(latest, candles, position, diagnostics)

        trend_up = (latest_close > ema_slow) and (ema_slow_slope > 0)
        pullback_ok = (
            (pullback_pct >= self.config.pullback_min_pct)
            and (pullback_pct <= self.config.pullback_max_pct)
            and (latest_close >= ema_fast * (1 - self.config.max_close_above_fast_ema_pct))
        )
        volatility_ok = (
            (atr_pct >= self.config.min_atr_pct)
            and (atr_pct <= self.config.max_atr_pct)
        )
        volume_ok = volume_ratio >= self.config.min_volume_ratio

        if self.config.use_breakout_trigger:
            trigger_long = latest_close > micro_high
        else:
            previous_close = closes[-2]
            previous_fast = ema_fast_values[-2]
            trigger_long = previous_fast is not None and (latest_close > ema_fast) and (previous_close <= previous_fast)

        diagnostics.update(
            {
                "trend_up": trend_up,
                "pullback_ok": pullback_ok,
                "volatility_ok": volatility_ok,
                "volume_ok": volume_ok,
                "trigger_long": trigger_long,
            }
        )

        should_enter = trend_up and pullback_ok and volatility_ok and volume_ok and trigger_long
        if not should_enter:
            return Signal(
                action="hold",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="TrendPullback",
                timestamp=latest.close_time,
                reason="filters_not_satisfied",
                metadata=diagnostics,
            )

        atr_stop = latest_close - self.config.atr_stop_mult * atr
        structural_stop = prior_low
        stop_price = min(structural_stop, atr_stop)
        if stop_price >= latest_close:
            return Signal(
                action="hold",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="TrendPullback",
                timestamp=latest.close_time,
                reason="invalid_stop",
                metadata=diagnostics,
            )

        take_price = latest_close + self.config.rr_target * (latest_close - stop_price)
        diagnostics.update(
            {
                "atr_stop": atr_stop,
                "structural_stop": structural_stop,
            }
        )

        return Signal(
            action="entry",
            symbol=self.symbol,
            timeframe=self.timeframe,
            strategy_name="TrendPullback",
            timestamp=latest.close_time,
            reason="long_entry",
            entry_price=latest_close,
            stop_price=stop_price,
            take_price=take_price,
            risk_per_unit=latest_close - stop_price,
            metadata=diagnostics,
        )

    def _evaluate_exit(
        self,
        latest: Candle,
        candles: list[Candle],
        position: PositionState,
        diagnostics: dict[str, float | bool],
    ) -> Signal:
        """Evaluate exit conditions in notebook order: stop, take, timeout."""

        bars_held = max(position.bars_held, self._bars_held(candles, position))
        diagnostics["bars_held"] = bars_held

        if latest.low <= position.stop_price:
            return Signal(
                action="exit",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="TrendPullback",
                timestamp=latest.close_time,
                reason="stop_loss",
                exit_price=position.stop_price,
                metadata=diagnostics,
            )

        if latest.high >= position.take_price:
            return Signal(
                action="exit",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="TrendPullback",
                timestamp=latest.close_time,
                reason="take_profit",
                exit_price=position.take_price,
                metadata=diagnostics,
            )

        if bars_held >= self.config.max_bars_in_trade:
            return Signal(
                action="exit",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="TrendPullback",
                timestamp=latest.close_time,
                reason="timeout",
                exit_price=latest.close,
                metadata=diagnostics,
            )

        return Signal(
            action="hold",
            symbol=self.symbol,
            timeframe=self.timeframe,
            strategy_name="TrendPullback",
            timestamp=latest.close_time,
            reason="position_open",
            metadata=diagnostics,
        )

    @staticmethod
    def _highest_excluding_current(values: list[float], lookback: int) -> float | None:
        if len(values) < lookback + 1:
            return None
        return max(values[-lookback - 1:-1])

    @staticmethod
    def _lowest_excluding_current(values: list[float], lookback: int) -> float | None:
        if len(values) < lookback + 1:
            return None
        return min(values[-lookback - 1:-1])

    @staticmethod
    def _bars_held(candles: list[Candle], position: PositionState) -> int:
        return sum(1 for candle in candles if candle.close_time > position.entry_time)
