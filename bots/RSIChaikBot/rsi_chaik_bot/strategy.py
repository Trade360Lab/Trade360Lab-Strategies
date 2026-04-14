"""Pure MACD + RSI reclaim strategy logic."""

from __future__ import annotations

from logging import Logger

from .config import StrategyConfig
from .models import Candle, PositionState, Signal


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


def _rsi_wilder(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if period <= 0 or len(values) <= period:
        return result

    gains: list[float] = []
    losses: list[float] = []
    for index in range(1, len(values)):
        change = values[index] - values[index - 1]
        gains.append(max(change, 0.0))
        losses.append(abs(min(change, 0.0)))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    result[period] = _rsi_from_averages(avg_gain, avg_loss)

    for index in range(period + 1, len(values)):
        gain = gains[index - 1]
        loss = losses[index - 1]
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
        result[index] = _rsi_from_averages(avg_gain, avg_loss)

    return result


def _rsi_from_averages(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _macd(
    values: list[float],
    fast_period: int,
    slow_period: int,
    signal_period: int,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    fast_values = _ema(values, fast_period)
    slow_values = _ema(values, slow_period)
    macd_line: list[float | None] = [None] * len(values)

    for index, (fast_value, slow_value) in enumerate(zip(fast_values, slow_values, strict=True)):
        if fast_value is None or slow_value is None:
            continue
        macd_line[index] = fast_value - slow_value

    signal_line = _ema([value or 0.0 for value in macd_line], signal_period)
    macd_hist: list[float | None] = [None] * len(values)

    for index, value in enumerate(macd_line):
        signal_value = signal_line[index]
        if value is None or signal_value is None:
            signal_line[index] = None
            continue
        macd_hist[index] = value - signal_value

    return macd_line, signal_line, macd_hist


class MACDRSIStrategy:
    """Long-only real-time port for the notebook MACD + RSI reclaim logic."""

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
                strategy_name="BTCMacdRsi",
                timestamp=latest.close_time,
                reason="warmup",
                metadata={"required_bars": self.config.warmup_bars, "available_bars": len(candles)},
            )

        closes = [candle.close for candle in candles]

        rsi_values = _rsi_wilder(closes, self.config.rsi_period)
        macd_line_values, macd_signal_values, macd_hist_values = _macd(
            closes,
            self.config.macd_fast,
            self.config.macd_slow,
            self.config.macd_signal,
        )
        atr_values = _atr_wilder(candles, self.config.atr_period)

        rsi = rsi_values[-1]
        previous_rsi = rsi_values[-2]
        macd_line = macd_line_values[-1]
        macd_signal = macd_signal_values[-1]
        atr = atr_values[-1]

        if None in {rsi, previous_rsi, macd_line, macd_signal, atr}:
            return Signal(
                action="hold",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="BTCMacdRsi",
                timestamp=latest.close_time,
                reason="indicator_unavailable",
            )

        diagnostics: dict[str, float | bool | str | list[str]] = {
            "close": float(latest.close),
            "rsi": float(rsi),
            "previous_rsi": float(previous_rsi),
            "macd_line": float(macd_line),
            "macd_signal": float(macd_signal),
            "atr": float(atr),
        }

        if position is not None:
            return self._evaluate_exit(latest, candles, position, diagnostics)

        macd_bullish = macd_line > macd_signal
        rsi_reclaim = previous_rsi <= self.config.rsi_entry_level < rsi

        diagnostics.update(
            {
                "macd_bullish": macd_bullish,
                "rsi_reclaim": rsi_reclaim,
            }
        )

        if not (macd_bullish and rsi_reclaim):
            return Signal(
                action="hold",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="BTCMacdRsi",
                timestamp=latest.close_time,
                reason="filters_not_satisfied",
                metadata=diagnostics,
            )

        atr_stop = latest.close - (self.config.atr_stop_mult * atr)
        stop_price = atr_stop
        if stop_price >= latest.close:
            return Signal(
                action="hold",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="BTCMacdRsi",
                timestamp=latest.close_time,
                reason="invalid_stop",
                metadata=diagnostics,
            )

        take_price = latest.close + self.config.rr_target * (latest.close - stop_price)
        diagnostics.update(
            {
                "atr_stop": float(atr_stop),
            }
        )

        return Signal(
            action="entry",
            symbol=self.symbol,
            timeframe=self.timeframe,
            strategy_name="BTCMacdRsi",
            timestamp=latest.close_time,
            reason="long_entry",
            entry_price=latest.close,
            stop_price=stop_price,
            take_price=take_price,
            risk_per_unit=latest.close - stop_price,
            metadata=diagnostics,
        )

    def _evaluate_exit(
        self,
        latest: Candle,
        candles: list[Candle],
        position: PositionState,
        diagnostics: dict[str, float | bool | str | list[str]],
    ) -> Signal:
        """Evaluate exits in runtime order: stop, take, signal, timeout."""

        bars_held = max(position.bars_held, self._bars_held(candles, position))
        diagnostics["bars_held"] = bars_held

        if latest.low <= position.stop_price:
            return Signal(
                action="exit",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="BTCMacdRsi",
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
                strategy_name="BTCMacdRsi",
                timestamp=latest.close_time,
                reason="take_profit",
                exit_price=position.take_price,
                metadata=diagnostics,
            )

        if self.config.enable_signal_exit:
            exit_reasons: list[str] = []
            macd_line = float(diagnostics["macd_line"])
            macd_signal = float(diagnostics["macd_signal"])
            rsi = float(diagnostics["rsi"])

            if macd_line < macd_signal:
                exit_reasons.append("macd_bearish")
            if rsi < self.config.rsi_exit_level:
                exit_reasons.append("rsi_lost_level")

            if exit_reasons:
                diagnostics["signal_exit_reasons"] = exit_reasons
                return Signal(
                    action="exit",
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                    strategy_name="BTCMacdRsi",
                    timestamp=latest.close_time,
                    reason="signal_exit",
                    exit_price=latest.close,
                    metadata=diagnostics,
                )

        if bars_held >= self.config.max_bars_in_trade:
            return Signal(
                action="exit",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="BTCMacdRsi",
                timestamp=latest.close_time,
                reason="timeout",
                exit_price=latest.close,
                metadata=diagnostics,
            )

        return Signal(
            action="hold",
            symbol=self.symbol,
            timeframe=self.timeframe,
            strategy_name="BTCMacdRsi",
            timestamp=latest.close_time,
            reason="position_open",
            metadata=diagnostics,
        )

    @staticmethod
    def _bars_held(candles: list[Candle], position: PositionState) -> int:
        return sum(1 for candle in candles if candle.close_time > position.entry_time)
