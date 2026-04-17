from __future__ import annotations

import logging
from typing import Any

import requests


LOGGER = logging.getLogger(__name__)
TELEGRAM_MESSAGE_LIMIT = 4096


def format_forecast_report(forecast: dict[str, Any], title: str = "BTC Daily Outlook") -> str:
    symbol = forecast["symbol"]
    timeframe = forecast["timeframe"]
    forecast_time = forecast["forecast_time"]

    prob_up = forecast["prob_up"] * 100
    prob_down = forecast["prob_down"] * 100
    prob_unsure = forecast["prob_unsure"] * 100

    decision = forecast["decision"]
    confidence = forecast["confidence"] * 100

    market_phase = forecast["market_phase"]
    volatility_regime = forecast["volatility_regime"]
    momentum_state = forecast["momentum_state"]
    model_version = forecast.get("model_version", "unknown")

    text = (
        f"{title}\n\n"
        f"Symbol: {symbol}\n"
        f"Timeframe: {timeframe}\n"
        f"Forecast time: {forecast_time}\n"
        f"Model version: {model_version}\n\n"
        f"Probabilities:\n"
        f"- UP: {prob_up:.2f}%\n"
        f"- DOWN: {prob_down:.2f}%\n"
        f"- UNSURE: {prob_unsure:.2f}%\n\n"
        f"Decision: {decision}\n"
        f"Confidence: {confidence:.2f}%\n\n"
        f"Market context:\n"
        f"- Phase: {market_phase}\n"
        f"- Volatility: {volatility_regime}\n"
        f"- Momentum: {momentum_state}\n"
    )
    return text


def print_report(report_text: str) -> None:
    print("=" * 60)
    print(report_text)
    print("=" * 60)


def _split_telegram_message(report_text: str) -> list[str]:
    if len(report_text) <= TELEGRAM_MESSAGE_LIMIT:
        return [report_text]

    chunks: list[str] = []
    remaining = report_text
    while len(remaining) > TELEGRAM_MESSAGE_LIMIT:
        split_at = remaining.rfind("\n", 0, TELEGRAM_MESSAGE_LIMIT)
        if split_at <= 0:
            split_at = TELEGRAM_MESSAGE_LIMIT
        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:].lstrip("\n")
    if remaining:
        chunks.append(remaining)
    return chunks


def send_telegram_report(
    report_text: str,
    enabled: bool,
    token: str,
    chat_id: str,
    timeout_seconds: int = 15,
    parse_mode: str | None = None,
) -> bool:
    if not enabled:
        LOGGER.info("Telegram sending is disabled by configuration.")
        return False
    if not token or not chat_id:
        LOGGER.warning("Telegram credentials are missing. Skipping Telegram send.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    chunks = _split_telegram_message(report_text)
    success = True

    for chunk in chunks:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": chunk}
        if parse_mode is not None:
            payload["parse_mode"] = parse_mode

        try:
            response = requests.post(url, json=payload, timeout=timeout_seconds)
            response.raise_for_status()
            LOGGER.info("Telegram report sent successfully.")
        except requests.RequestException as exc:
            LOGGER.exception("Telegram send failed: %s", exc)
            success = False
            break

    return success
