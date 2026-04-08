import os
import requests
from typing import Dict, Any


def format_forecast_report(forecast: Dict[str, Any]) -> str:
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
        f"BTC Daily Outlook\n\n"
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


def send_telegram_report(report_text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram credentials not found, skipping Telegram send.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": report_text,
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        print(f"Telegram send failed: {exc}")
        return False