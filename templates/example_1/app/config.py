"""Application configuration for the backtesting template."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "outputs"
DEFAULT_LOG_DIR = DEFAULT_OUTPUT_DIR / "logs"
DEFAULT_REPORTS_DIR = DEFAULT_OUTPUT_DIR / "reports"

load_dotenv(PROJECT_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default).lower()).lower() == "true"


@dataclass(slots=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    strategy_name: str = field(default_factory=lambda: os.getenv("STRATEGY_NAME", "sma_cross"))
    data_path: str = field(default_factory=lambda: os.getenv("DATA_PATH", "data/btcusdt_1h.csv"))
    cash: float = field(default_factory=lambda: float(os.getenv("CASH", "10000")))
    commission: float = field(default_factory=lambda: float(os.getenv("COMMISSION", "0.001")))
    stake: float = field(default_factory=lambda: float(os.getenv("STAKE", "1")))
    plot: bool = field(default_factory=lambda: _env_bool("PLOT", False))
    output_dir: Path = field(
        default_factory=lambda: Path(os.getenv("OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR)))
    )
    log_dir: Path = field(
        default_factory=lambda: Path(os.getenv("LOG_DIR", str(DEFAULT_LOG_DIR)))
    )
    reports_dir: Path = field(
        default_factory=lambda: Path(os.getenv("REPORTS_DIR", str(DEFAULT_REPORTS_DIR)))
    )
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    enable_event_logging: bool = field(
        default_factory=lambda: _env_bool("ENABLE_EVENT_LOGGING", True)
    )
    enable_bar_logging: bool = field(
        default_factory=lambda: _env_bool("ENABLE_BAR_LOGGING", False)
    )
    symbol: str = field(default_factory=lambda: os.getenv("SYMBOL", "BTCUSDT"))
    timeframe: str = field(default_factory=lambda: os.getenv("TIMEFRAME", "1h"))

    def __post_init__(self) -> None:
        self.output_dir = self._resolve_path(self.output_dir)
        self.log_dir = self._resolve_path(self.log_dir)
        self.reports_dir = self._resolve_path(self.reports_dir)
        self.data_path = str(self._resolve_path(Path(self.data_path)))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    @property
    def log_file(self) -> Path:
        return self.log_dir / "strategy.log"

    @property
    def summary_report_path(self) -> Path:
        return self.reports_dir / "summary.json"

    @property
    def trades_report_path(self) -> Path:
        return self.reports_dir / "trades.csv"

    @property
    def equity_report_path(self) -> Path:
        return self.reports_dir / "equity_curve.csv"

    def _resolve_path(self, path: Path) -> Path:
        return path if path.is_absolute() else (PROJECT_DIR / path).resolve()
