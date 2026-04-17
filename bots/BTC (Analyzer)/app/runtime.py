from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.binance_loader import load_binance_klines, validate_ohlcv
from app.predictor import predict_latest_forecast
from app.reporter import format_forecast_report, print_report, send_telegram_report
from app.settings import SettingsError, configure_logging, load_runtime_settings


LOGGER = logging.getLogger(__name__)
FORECAST_HISTORY_FILE = "forecast_history.jsonl"


def persist_forecast_history(logs_dir: Path, forecast: dict[str, Any]) -> Path:
    logs_dir.mkdir(parents=True, exist_ok=True)
    target_path = logs_dir / FORECAST_HISTORY_FILE
    payload = {
        "forecast_time": forecast["forecast_time"],
        "symbol": forecast["symbol"],
        "timeframe": forecast["timeframe"],
        "decision": forecast["decision"],
        "confidence": forecast["confidence"],
        "prob_up": forecast["prob_up"],
        "prob_down": forecast["prob_down"],
        "prob_unsure": forecast["prob_unsure"],
        "market_phase": forecast["market_phase"],
        "volatility_regime": forecast["volatility_regime"],
        "momentum_state": forecast["momentum_state"],
        "model_version": forecast["model_version"],
        "latest_close": forecast["latest_close"],
        "last_candle_time": forecast["last_candle_time"],
    }
    with target_path.open("a", encoding="utf-8") as file_obj:
        file_obj.write(json.dumps(payload, ensure_ascii=True) + "\n")
    return target_path


def main() -> None:
    try:
        settings = load_runtime_settings()
        configure_logging(settings.log_level)
    except SettingsError as exc:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        logging.getLogger(__name__).error("Startup validation failed: %s", exc)
        raise

    LOGGER.info(
        "Starting BTC analyzer: symbol=%s timeframe=%s lookback=%s dry_run=%s",
        settings.binance_symbol,
        settings.binance_interval,
        settings.lookback_bars,
        settings.dry_run,
    )
    LOGGER.info("Loading market data from Binance")
    df = load_binance_klines(
        symbol=settings.binance_symbol,
        interval=settings.binance_interval,
        limit_total=settings.lookback_bars,
        timeout_seconds=settings.request_timeout_seconds,
        use_closed_candle_only=settings.use_closed_candle_only,
    )
    df = validate_ohlcv(df, expected_freq=settings.expected_freq)

    LOGGER.info("Generating forecast using model artifacts from %s", settings.artifacts_dir)
    forecast = predict_latest_forecast(
        df=df,
        artifacts_dir=settings.artifacts_dir,
        decision_margin_override=settings.decision_margin,
    )
    history_path = persist_forecast_history(settings.logs_dir, forecast)
    LOGGER.info("Forecast appended to %s", history_path)

    report_text = format_forecast_report(forecast, title=settings.report_title)
    print_report(report_text)
    send_telegram_report(
        report_text=report_text,
        enabled=settings.telegram_enabled and not settings.dry_run,
        token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
        timeout_seconds=settings.request_timeout_seconds,
    )
