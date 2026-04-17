from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_ARTIFACTS_DIR = Path("artifacts")
DEFAULT_LOGS_DIR = Path("logs")
DEFAULT_REQUEST_TIMEOUT_SECONDS = 20
MIN_LOOKBACK_BARS = 100


class SettingsError(ValueError):
    pass


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise SettingsError(f"Invalid boolean value: {value!r}")


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise SettingsError(f"Invalid integer value: {value!r}") from exc


def _parse_float(value: str | None, default: float) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise SettingsError(f"Invalid float value: {value!r}") from exc


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


@dataclass(frozen=True)
class RuntimeSettings:
    artifacts_dir: Path
    logs_dir: Path
    telegram_enabled: bool
    telegram_bot_token: str
    telegram_chat_id: str
    binance_symbol: str
    binance_interval: str
    lookback_bars: int
    decision_margin: float
    request_timeout_seconds: int
    log_level: str
    dry_run: bool
    tz: str
    expected_freq: str
    report_title: str
    use_closed_candle_only: bool
    model_meta: dict[str, Any]
    training_config: dict[str, Any]
    decision_config: dict[str, Any]

    @property
    def model_path(self) -> Path:
        return self.artifacts_dir / "model.pkl"


def load_runtime_settings() -> RuntimeSettings:
    artifacts_dir = Path(os.getenv("ARTIFACTS_DIR", str(DEFAULT_ARTIFACTS_DIR)))
    logs_dir = DEFAULT_LOGS_DIR

    model_meta_path = artifacts_dir / "model_meta.json"
    training_config_path = artifacts_dir / "training_config.json"
    decision_config_path = artifacts_dir / "decision_config.json"

    model_meta = load_json(model_meta_path) if model_meta_path.exists() else {}
    training_config = load_json(training_config_path) if training_config_path.exists() else {}
    decision_config = load_json(decision_config_path) if decision_config_path.exists() else {}

    symbol = os.getenv("BINANCE_SYMBOL") or str(model_meta.get("symbol", "BTCUSDT"))
    interval = os.getenv("BINANCE_INTERVAL") or str(model_meta.get("timeframe", "1h"))
    lookback_bars = _parse_int(os.getenv("LOOKBACK_BARS"), int(training_config.get("lookback_bars", 500)))
    decision_margin = _parse_float(
        os.getenv("DECISION_MARGIN"),
        float(decision_config.get("decision_margin", training_config.get("decision_margin", 0.10))),
    )
    request_timeout_seconds = _parse_int(
        os.getenv("REQUEST_TIMEOUT_SECONDS"),
        DEFAULT_REQUEST_TIMEOUT_SECONDS,
    )
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    dry_run = _parse_bool(os.getenv("DRY_RUN"), False)
    telegram_enabled = _parse_bool(
        os.getenv("TELEGRAM_ENABLED"),
        bool(decision_config.get("telegram_enabled_default", False)),
    )
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    tz = os.getenv("TZ", "UTC")
    expected_freq = str(training_config.get("expected_freq", interval))
    report_title = str(decision_config.get("report_title", "BTC Daily Outlook"))
    use_closed_candle_only = _parse_bool(
        os.getenv("USE_CLOSED_CANDLE_ONLY"),
        bool(decision_config.get("use_closed_candle_only", True)),
    )

    settings = RuntimeSettings(
        artifacts_dir=artifacts_dir,
        logs_dir=logs_dir,
        telegram_enabled=telegram_enabled,
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id,
        binance_symbol=symbol,
        binance_interval=interval,
        lookback_bars=lookback_bars,
        decision_margin=decision_margin,
        request_timeout_seconds=request_timeout_seconds,
        log_level=log_level,
        dry_run=dry_run,
        tz=tz,
        expected_freq=expected_freq,
        report_title=report_title,
        use_closed_candle_only=use_closed_candle_only,
        model_meta=model_meta,
        training_config=training_config,
        decision_config=decision_config,
    )
    validate_runtime_settings(settings)
    return settings


def validate_runtime_settings(settings: RuntimeSettings) -> None:
    required_paths = [
        settings.artifacts_dir / "feature_columns.json",
        settings.artifacts_dir / "model_meta.json",
        settings.artifacts_dir / "training_config.json",
        settings.artifacts_dir / "decision_config.json",
    ]
    if not settings.artifacts_dir.exists():
        raise SettingsError(f"Artifacts directory not found: {settings.artifacts_dir}")

    missing_files = [path.name for path in required_paths if not path.exists()]
    if missing_files:
        raise SettingsError(f"Missing required artifact files: {', '.join(missing_files)}")

    if not settings.model_path.exists():
        legacy_model = settings.artifacts_dir / "model.json"
        if legacy_model.exists():
            raise SettingsError(
                f"Missing model.pkl in {settings.artifacts_dir}. Found legacy file {legacy_model.name}, "
                "but runtime requires a valid joblib-exported model.pkl."
            )
        raise SettingsError(f"Missing required model artifact: {settings.model_path}")

    feature_columns = load_json(settings.artifacts_dir / "feature_columns.json")
    if not isinstance(feature_columns, list) or not feature_columns:
        raise SettingsError("feature_columns.json must contain a non-empty JSON array.")

    if not settings.binance_symbol:
        raise SettingsError("BINANCE_SYMBOL is required.")
    if not settings.binance_interval:
        raise SettingsError("BINANCE_INTERVAL is required.")
    if settings.lookback_bars < MIN_LOOKBACK_BARS:
        raise SettingsError(
            f"LOOKBACK_BARS must be >= {MIN_LOOKBACK_BARS} to support rolling feature windows."
        )
    if settings.request_timeout_seconds <= 0:
        raise SettingsError("REQUEST_TIMEOUT_SECONDS must be positive.")
    if settings.decision_margin < 0:
        raise SettingsError("DECISION_MARGIN must be non-negative.")

    valid_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
    if settings.log_level not in valid_levels:
        raise SettingsError(f"LOG_LEVEL must be one of: {', '.join(sorted(valid_levels))}")


def configure_logging(log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
