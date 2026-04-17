from app.reporter import build_telegram_reply_markup, format_forecast_report


def test_reporter_format() -> None:
    forecast = {
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "forecast_time": "2026-04-17T00:00:00+00:00",
        "prob_up": 0.4,
        "prob_down": 0.3,
        "prob_unsure": 0.3,
        "decision": "UP",
        "confidence": 0.1,
        "market_phase": "bullish",
        "volatility_regime": "normal",
        "momentum_state": "positive",
        "model_version": "btc_h1_xgb_v1",
    }

    report = format_forecast_report(forecast)

    assert "BTC Daily Outlook" in report
    assert "Decision: UP" in report
    assert "Model version: btc_h1_xgb_v1" in report


def test_telegram_reply_markup_contains_buttons() -> None:
    reply_markup = build_telegram_reply_markup("BTCUSDT")

    assert reply_markup is not None
    assert "inline_keyboard" in reply_markup
    buttons = reply_markup["inline_keyboard"][0]
    assert buttons[0]["text"] == "Open Binance"
    assert "BTC_USDT" in buttons[0]["url"]
    assert buttons[1]["text"] == "Open TradingView"
    assert "BINANCE%3ABTCUSDT" in buttons[1]["url"]
