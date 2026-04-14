"""Pure RSI + MACD + Chaikin strategy logic."""

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


def _cmf(candles: list[Candle], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(candles)
    if period <= 0 or len(candles) < period:
        return result

    money_flow_volume: list[float] = []
    volumes: list[float] = []
    for candle in candles:
        if candle.high == candle.low:
            multiplier = 0.0
        else:
            multiplier = ((candle.close - candle.low) - (candle.high - candle.close)) / (candle.high - candle.low)
        money_flow_volume.append(multiplier * candle.volume)
        volumes.append(candle.volume)

    rolling_mfv = sum(money_flow_volume[:period])
    rolling_volume = sum(volumes[:period])
    result[period - 1] = (rolling_mfv / rolling_volume) if rolling_volume > 0 else 0.0

    for index in range(period, len(candles)):
        rolling_mfv += money_flow_volume[index] - money_flow_volume[index - period]
        rolling_volume += volumes[index] - volumes[index - period]
        result[index] = (rolling_mfv / rolling_volume) if rolling_volume > 0 else 0.0

    return result


def _adl(candles: list[Candle]) -> list[float]:
    result: list[float] = []
    running = 0.0
    for candle in candles:
        if candle.high == candle.low:
            multiplier = 0.0
        else:
            multiplier = ((candle.close - candle.low) - (candle.high - candle.close)) / (candle.high - candle.low)
        running += multiplier * candle.volume
        result.append(running)
    return result


def _chaikin_oscillator(candles: list[Candle], fast_period: int, slow_period: int) -> list[float | None]:
    adl_values = _adl(candles)
    fast_values = _ema(adl_values, fast_period)
    slow_values = _ema(adl_values, slow_period)
    result: list[float | None] = [None] * len(candles)

    for index, (fast_value, slow_value) in enumerate(zip(fast_values, slow_values, strict=True)):
        if fast_value is None or slow_value is None:
            continue
        result[index] = fast_value - slow_value
    return result


class RSIMACDChaikinStrategy:
    """Long-only real-time port for RSI + MACD + Chaikin confirmation."""

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
                strategy_name="RSIMACDChaikin",
                timestamp=latest.close_time,
                reason="warmup",
                metadata={"required_bars": self.config.warmup_bars, "available_bars": len(candles)},
            )

        closes = [candle.close for candle in candles]
        lows = [candle.low for candle in candles]

        rsi_values = _rsi_wilder(closes, self.config.rsi_period)
        macd_line_values, macd_signal_values, macd_hist_values = _macd(
            closes,
            self.config.macd_fast,
            self.config.macd_slow,
            self.config.macd_signal,
        )
        cmf_values = _cmf(candles, self.config.cmf_period)
        chaikin_osc_values = _chaikin_oscillator(
            candles,
            self.config.chaikin_osc_fast,
            self.config.chaikin_osc_slow,
        )
        atr_values = _atr_wilder(candles, self.config.atr_period)

        rsi = rsi_values[-1]
        previous_rsi = rsi_values[-2]
        macd_line = macd_line_values[-1]
        macd_signal = macd_signal_values[-1]
        macd_hist = macd_hist_values[-1]
        previous_hist = macd_hist_values[-2]
        atr = atr_values[-1]
        chaikin_value = cmf_values[-1] if self.config.chaikin_confirmation == "cmf" else chaikin_osc_values[-1]
        recent_swing_low = self._lowest_excluding_current(lows, self.config.swing_window)

        if None in {rsi, previous_rsi, macd_line, macd_signal, macd_hist, atr, chaikin_value, recent_swing_low}:
            return Signal(
                action="hold",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="RSIMACDChaikin",
                timestamp=latest.close_time,
                reason="indicator_unavailable",
            )

        diagnostics: dict[str, float | bool | str | list[str]] = {
            "close": float(latest.close),
            "rsi": float(rsi),
            "previous_rsi": float(previous_rsi),
            "macd_line": float(macd_line),
            "macd_signal": float(macd_signal),
            "macd_hist": float(macd_hist),
            "chaikin_mode": self.config.chaikin_confirmation,
            "chaikin_value": float(chaikin_value),
            "atr": float(atr),
            "recent_swing_low": float(recent_swing_low),
        }

        if position is not None:
            return self._evaluate_exit(latest, candles, position, diagnostics)

        macd_bullish = (macd_line > macd_signal) and (
            (not self.config.require_macd_hist_positive) or (macd_hist > 0)
        )
        if self.config.require_macd_hist_rising:
            macd_bullish = macd_bullish and previous_hist is not None and macd_hist >= previous_hist

        rsi_reclaim = previous_rsi <= self.config.rsi_reclaim_level < rsi
        chaikin_confirmed = chaikin_value > self.config.chaikin_entry_threshold

        diagnostics.update(
            {
                "macd_bullish": macd_bullish,
                "rsi_reclaim": rsi_reclaim,
                "chaikin_confirmed": chaikin_confirmed,
            }
        )

        if not (macd_bullish and rsi_reclaim and chaikin_confirmed):
            return Signal(
                action="hold",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="RSIMACDChaikin",
                timestamp=latest.close_time,
                reason="filters_not_satisfied",
                metadata=diagnostics,
            )

        structural_stop = recent_swing_low * (1.0 - self.config.structural_stop_buffer_pct)
        atr_stop = latest.close - (self.config.atr_stop_mult * atr)
        stop_price = min(structural_stop, atr_stop)
        if stop_price >= latest.close:
            return Signal(
                action="hold",
                symbol=self.symbol,
                timeframe=self.timeframe,
                strategy_name="RSIMACDChaikin",
                timestamp=latest.close_time,
                reason="invalid_stop",
                metadata=diagnostics,
            )

        take_price = latest.close + self.config.rr_target * (latest.close - stop_price)
        diagnostics.update(
            {
                "structural_stop": float(structural_stop),
                "atr_stop": float(atr_stop),
            }
        )

        return Signal(
            action="entry",
            symbol=self.symbol,
            timeframe=self.timeframe,
            strategy_name="RSIMACDChaikin",
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
                strategy_name="RSIMACDChaikin",
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
                strategy_name="RSIMACDChaikin",
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
            chaikin_value = float(diagnostics["chaikin_value"])

            if self.config.signal_exit_on_macd_bearish and macd_line < macd_signal:
                exit_reasons.append("macd_bearish")
            if self.config.signal_exit_on_rsi_loss and rsi < self.config.rsi_exit_level:
                exit_reasons.append("rsi_lost_level")
            if self.config.signal_exit_on_chaikin_loss and chaikin_value <= self.config.chaikin_exit_threshold:
                exit_reasons.append("chaikin_lost_confirmation")

            if exit_reasons:
                diagnostics["signal_exit_reasons"] = exit_reasons
                return Signal(
                    action="exit",
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                    strategy_name="RSIMACDChaikin",
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
                strategy_name="RSIMACDChaikin",
                timestamp=latest.close_time,
                reason="timeout",
                exit_price=latest.close,
                metadata=diagnostics,
            )

        return Signal(
            action="hold",
            symbol=self.symbol,
            timeframe=self.timeframe,
            strategy_name="RSIMACDChaikin",
            timestamp=latest.close_time,
            reason="position_open",
            metadata=diagnostics,
        )

    @staticmethod
    def _lowest_excluding_current(values: list[float], lookback: int) -> float | None:
        if len(values) < lookback + 1:
            return None
        return min(values[-lookback - 1:-1])

    @staticmethod
    def _bars_held(candles: list[Candle], position: PositionState) -> int:
        return sum(1 for candle in candles if candle.close_time > position.entry_time)
