"""Application configuration for PullbackTrader."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value not in {None, ""} else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value not in {None, ""} else default


@dataclass(slots=True)
class StrategyConfig:
    """Notebook-equivalent strategy parameters."""

    ema_fast: int = 20
    ema_slow: int = 200
    atr_period: int = 14
    volume_window: int = 20
    swing_window: int = 10
    slope_lookback: int = 10
    pullback_min_pct: float = 0.003
    pullback_max_pct: float = 0.03
    max_close_above_fast_ema_pct: float = 0.01
    min_volume_ratio: float = 1.0
    min_atr_pct: float = 0.002
    max_atr_pct: float = 0.08
    use_breakout_trigger: bool = True
    risk_per_trade: float = 0.01
    rr_target: float = 2.0
    atr_stop_mult: float = 1.5
    max_bars_in_trade: int = 100
    debug: bool = False

    @property
    def warmup_bars(self) -> int:
        """Minimum candle count required to evaluate all indicators."""

        return max(
            self.ema_slow + self.slope_lookback + 2,
            self.ema_fast + 2,
            self.atr_period + 2,
            self.volume_window + 2,
            self.swing_window + 2,
            max(3, self.swing_window // 2) + 2,
        )


@dataclass(slots=True)
class MarketConfig:
    """Market data settings."""

    symbol: str = "BTCUSDT"
    timeframe: str = "5m"
    history_limit: int = 600
    poll_interval_seconds: float = 2.0
    request_timeout_seconds: float = 20.0
    retry_sleep_seconds: float = 3.0
    binance_rest_url: str = "https://api.binance.com/api/v3/klines"


@dataclass(slots=True)
class ExecutionConfig:
    """Order execution settings."""

    paper_mode: bool = True
    initial_cash: float = 10_000.0
    fee_rate: float = 0.0004
    slippage_pct: float = 0.0002
    price_step: float = 0.10
    quantity_step: float = 0.00001
    min_quantity: float = 0.00001
    api_key: str = ""
    api_secret: str = ""
    live_base_url: str = "https://api.binance.com"


@dataclass(slots=True)
class StorageConfig:
    """Persistent storage settings."""

    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: str = "data"
    logs_dir: str = "logs"
    state_dir: str = "state"
    state_file_name: str = "bot_state.json"
    signals_file_name: str = "signals.csv"
    trades_file_name: str = "trades.csv"

    @property
    def data_path(self) -> Path:
        return self.project_root / self.data_dir

    @property
    def logs_path(self) -> Path:
        return self.project_root / self.logs_dir

    @property
    def state_path(self) -> Path:
        return self.project_root / self.state_dir

    @property
    def state_file(self) -> Path:
        return self.state_path / self.state_file_name

    @property
    def signals_file(self) -> Path:
        return self.data_path / self.signals_file_name

    @property
    def trades_file(self) -> Path:
        return self.data_path / self.trades_file_name


@dataclass(slots=True)
class AppConfig:
    """Top-level runtime configuration."""

    app_name: str = "PullbackTrader"
    strategy_name: str = "TrendPullback"
    log_level: str = "INFO"
    kill_switch: bool = False
    loop_error_sleep_seconds: float = 5.0
    market: MarketConfig = field(default_factory=MarketConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""

        load_dotenv()

        config = cls(
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            kill_switch=_env_bool("KILL_SWITCH", False),
            loop_error_sleep_seconds=_env_float("LOOP_ERROR_SLEEP_SECONDS", 5.0),
            market=MarketConfig(
                symbol=os.getenv("SYMBOL", "BTCUSDT").upper(),
                timeframe=os.getenv("TIMEFRAME", "5m"),
                history_limit=_env_int("HISTORY_LIMIT", 600),
                poll_interval_seconds=_env_float("POLL_INTERVAL_SECONDS", 2.0),
                request_timeout_seconds=_env_float("REQUEST_TIMEOUT_SECONDS", 20.0),
                retry_sleep_seconds=_env_float("RETRY_SLEEP_SECONDS", 3.0),
                binance_rest_url=os.getenv(
                    "BINANCE_REST_URL",
                    "https://api.binance.com/api/v3/klines",
                ),
            ),
            strategy=StrategyConfig(
                ema_fast=_env_int("EMA_FAST", 20),
                ema_slow=_env_int("EMA_SLOW", 200),
                atr_period=_env_int("ATR_PERIOD", 14),
                volume_window=_env_int("VOLUME_WINDOW", 20),
                swing_window=_env_int("SWING_WINDOW", 10),
                slope_lookback=_env_int("SLOPE_LOOKBACK", 10),
                pullback_min_pct=_env_float("PULLBACK_MIN_PCT", 0.003),
                pullback_max_pct=_env_float("PULLBACK_MAX_PCT", 0.03),
                max_close_above_fast_ema_pct=_env_float("MAX_CLOSE_ABOVE_FAST_EMA_PCT", 0.01),
                min_volume_ratio=_env_float("MIN_VOLUME_RATIO", 1.0),
                min_atr_pct=_env_float("MIN_ATR_PCT", 0.002),
                max_atr_pct=_env_float("MAX_ATR_PCT", 0.08),
                use_breakout_trigger=_env_bool("USE_BREAKOUT_TRIGGER", True),
                risk_per_trade=_env_float("RISK_PER_TRADE", 0.01),
                rr_target=_env_float("RR_TARGET", 2.0),
                atr_stop_mult=_env_float("ATR_STOP_MULT", 1.5),
                max_bars_in_trade=_env_int("MAX_BARS_IN_TRADE", 100),
                debug=_env_bool("STRATEGY_DEBUG", False),
            ),
            execution=ExecutionConfig(
                paper_mode=_env_bool("PAPER_MODE", True),
                initial_cash=_env_float("INITIAL_CASH", 10_000.0),
                fee_rate=_env_float("FEE_RATE", 0.0004),
                slippage_pct=_env_float("SLIPPAGE_PCT", 0.0002),
                price_step=_env_float("PRICE_STEP", 0.10),
                quantity_step=_env_float("QUANTITY_STEP", 0.00001),
                min_quantity=_env_float("MIN_QUANTITY", 0.00001),
                api_key=os.getenv("API_KEY", ""),
                api_secret=os.getenv("API_SECRET", ""),
                live_base_url=os.getenv("LIVE_BASE_URL", "https://api.binance.com"),
            ),
            storage=StorageConfig(
                project_root=Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parent.parent)),
                data_dir=os.getenv("DATA_DIR", "data"),
                logs_dir=os.getenv("LOGS_DIR", "logs"),
                state_dir=os.getenv("STATE_DIR", "state"),
                state_file_name=os.getenv("STATE_FILE", "bot_state.json"),
                signals_file_name=os.getenv("SIGNALS_FILE", "signals.csv"),
                trades_file_name=os.getenv("TRADES_FILE", "trades.csv"),
            ),
        )
        config.validate()
        return config

    def validate(self) -> None:
        """Validate a coherent runtime configuration."""

        if self.strategy.ema_fast >= self.strategy.ema_slow:
            raise ValueError("EMA_FAST must be smaller than EMA_SLOW.")
        if self.strategy.pullback_min_pct >= self.strategy.pullback_max_pct:
            raise ValueError("PULLBACK_MIN_PCT must be smaller than PULLBACK_MAX_PCT.")
        if self.execution.initial_cash <= 0:
            raise ValueError("INITIAL_CASH must be positive.")
        if self.execution.quantity_step <= 0 or self.execution.price_step <= 0:
            raise ValueError("PRICE_STEP and QUANTITY_STEP must be positive.")
