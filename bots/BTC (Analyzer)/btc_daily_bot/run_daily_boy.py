import json
from pathlib import Path

from binance_loader import load_binance_klines, validate_ohlcv
from predictor import predict_latest_forecast
from reporter import format_forecast_report, print_report, send_telegram_report


ARTIFACTS_DIR = Path("artifacts")


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    model_meta = load_json(ARTIFACTS_DIR / "model_meta.json")
    training_config = load_json(ARTIFACTS_DIR / "training_config.json")

    symbol = model_meta["symbol"]
    timeframe = model_meta["timeframe"]
    lookback_bars = training_config["lookback_bars"]

    expected_freq = training_config["expected_freq"]

    print(f"Loading market data: symbol={symbol}, timeframe={timeframe}, lookback={lookback_bars}")

    df = load_binance_klines(
        symbol=symbol,
        interval=timeframe,
        limit_total=lookback_bars,
    )
    df = validate_ohlcv(df, expected_freq=expected_freq)

    forecast = predict_latest_forecast(
        df=df,
        artifacts_dir=ARTIFACTS_DIR,
    )

    report_text = format_forecast_report(forecast)

    print_report(report_text)
    send_telegram_report(report_text)


if __name__ == "__main__":
    main()