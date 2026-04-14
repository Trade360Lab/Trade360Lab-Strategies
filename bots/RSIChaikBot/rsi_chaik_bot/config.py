"""Application configuration for RSIChaikBot."""

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
    """Strategy parameters ported into runtime configuration."""

    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    rsi_period: int = 14
    rsi_entry_level: float = 45.0
    rsi_exit_level: float = 40.0
    atr_period: int = 14
    atr_stop_mult: float = 1.5
    enable_signal_exit: bool = True
    risk_per_trade: float = 0.01
    rr_target: float = 1.5
    max_bars_in_trade: int = 72
    debug: bool = False

    @property
    def warmup_bars(self) -> int:
        """Minimum amount of candles needed to evaluate the strategy."""

        return max(
            self.macd_slow + self.macd_signal + 3,
            self.rsi_period + 3,
            self.atr_period + 3,
        )


@dataclass(slots=True)
class MarketConfig:
    """Market data settings."""

    symbol: str = "BTCUSDT"
    timeframe: str = "15m"
    history_limit: int = 400
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

    app_name: str = "RSIChaikBot"
    strategy_name: str = "BTCMacdRsi"
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
                timeframe=os.getenv("TIMEFRAME", "15m"),
                history_limit=_env_int("HISTORY_LIMIT", 400),
                poll_interval_seconds=_env_float("POLL_INTERVAL_SECONDS", 2.0),
                request_timeout_seconds=_env_float("REQUEST_TIMEOUT_SECONDS", 20.0),
                retry_sleep_seconds=_env_float("RETRY_SLEEP_SECONDS", 3.0),
                binance_rest_url=os.getenv(
                    "BINANCE_REST_URL",
                    "https://api.binance.com/api/v3/klines",
                ),
            ),
            strategy=StrategyConfig(
                macd_fast=_env_int("MACD_FAST", 12),
                macd_slow=_env_int("MACD_SLOW", 26),
                macd_signal=_env_int("MACD_SIGNAL", 9),
                rsi_period=_env_int("RSI_PERIOD", 14),
                rsi_entry_level=_env_float("RSI_ENTRY_LEVEL", 45.0),
                rsi_exit_level=_env_float("RSI_EXIT_LEVEL", 40.0),
                atr_period=_env_int("ATR_PERIOD", 14),
                atr_stop_mult=_env_float("ATR_STOP_MULT", 1.5),
                enable_signal_exit=_env_bool("ENABLE_SIGNAL_EXIT", True),
                risk_per_trade=_env_float("RISK_PER_TRADE", 0.01),
                rr_target=_env_float("RR_TARGET", 1.5),
                max_bars_in_trade=_env_int("MAX_BARS_IN_TRADE", 72),
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

        if self.strategy.macd_fast >= self.strategy.macd_slow:
            raise ValueError("MACD_FAST must be smaller than MACD_SLOW.")
        if self.strategy.macd_signal <= 0:
            raise ValueError("MACD_SIGNAL must be positive.")
        if self.strategy.rsi_period <= 1:
            raise ValueError("RSI_PERIOD must be greater than 1.")
        if not 0.0 <= self.strategy.rsi_entry_level <= 100.0:
            raise ValueError("RSI_ENTRY_LEVEL must be between 0 and 100.")
        if not 0.0 <= self.strategy.rsi_exit_level <= 100.0:
            raise ValueError("RSI_EXIT_LEVEL must be between 0 and 100.")
        if self.strategy.rsi_exit_level >= self.strategy.rsi_entry_level:
            raise ValueError("RSI_EXIT_LEVEL must be smaller than RSI_ENTRY_LEVEL.")
        if self.strategy.atr_period <= 0:
            raise ValueError("ATR_PERIOD must be positive.")
        if not 0.0 < self.strategy.risk_per_trade <= 1.0:
            raise ValueError("RISK_PER_TRADE must be between 0 and 1.")
        if self.strategy.rr_target <= 0:
            raise ValueError("RR_TARGET must be positive.")
        if self.strategy.max_bars_in_trade <= 0:
            raise ValueError("MAX_BARS_IN_TRADE must be positive.")
        if self.execution.initial_cash <= 0:
            raise ValueError("INITIAL_CASH must be positive.")
        if self.execution.quantity_step <= 0 or self.execution.price_step <= 0:
            raise ValueError("PRICE_STEP and QUANTITY_STEP must be positive.")
        if self.market.history_limit < self.strategy.warmup_bars:
            raise ValueError("HISTORY_LIMIT must be greater than or equal to strategy warmup bars.")
