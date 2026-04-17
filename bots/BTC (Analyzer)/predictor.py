from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()

    x["ret_1"] = x["close"].pct_change(1)
    x["ret_2"] = x["close"].pct_change(2)
    x["ret_3"] = x["close"].pct_change(3)
    x["ret_5"] = x["close"].pct_change(5)
    x["ret_10"] = x["close"].pct_change(10)

    x["hl_range"] = (x["high"] - x["low"]) / x["close"]
    x["body"] = (x["close"] - x["open"]) / x["open"]
    x["upper_wick"] = (x["high"] - x[["open", "close"]].max(axis=1)) / x["close"]
    x["lower_wick"] = (x[["open", "close"]].min(axis=1) - x["low"]) / x["close"]

    x["ema_9"] = x["close"].ewm(span=9, adjust=False).mean()
    x["ema_21"] = x["close"].ewm(span=21, adjust=False).mean()
    x["ema_50"] = x["close"].ewm(span=50, adjust=False).mean()

    x["dist_ema_9"] = (x["close"] - x["ema_9"]) / x["ema_9"]
    x["dist_ema_21"] = (x["close"] - x["ema_21"]) / x["ema_21"]
    x["dist_ema_50"] = (x["close"] - x["ema_50"]) / x["ema_50"]

    x["ema_spread_9_21"] = (x["ema_9"] - x["ema_21"]) / x["ema_21"]
    x["ema_spread_21_50"] = (x["ema_21"] - x["ema_50"]) / x["ema_50"]

    x["rsi_14"] = compute_rsi(x["close"], period=14)
    x["rsi_14_lag1"] = x["rsi_14"].shift(1)

    x["volatility_10"] = x["ret_1"].rolling(10).std()
    x["volatility_20"] = x["ret_1"].rolling(20).std()
    x["volatility_regime"] = (x["volatility_10"] > x["volatility_20"]).astype(int)

    x["volume_ma_20"] = x["volume"].rolling(20).mean()
    x["volume_ratio"] = x["volume"] / x["volume_ma_20"]
    x["volume_ratio_lag1"] = x["volume_ratio"].shift(1)

    x["rolling_high_20"] = x["high"].rolling(20).max()
    x["rolling_low_20"] = x["low"].rolling(20).min()
    x["dist_high_20"] = (x["close"] - x["rolling_high_20"]) / x["rolling_high_20"]
    x["dist_low_20"] = (x["close"] - x["rolling_low_20"]) / x["rolling_low_20"]

    x["trend_strength"] = x["ema_spread_9_21"].abs()
    x["ret_acceleration"] = x["ret_1"] - x["ret_3"]

    x["hour"] = x.index.hour
    x["dayofweek"] = x.index.dayofweek

    x = x.dropna().copy()
    return x


def apply_decision_layer(prob_down: float, prob_unsure: float, prob_up: float, margin: float) -> str:
    probs = [prob_down, prob_unsure, prob_up]
    top = max(probs)
    second = sorted(probs)[-2]

    if (top - second) < margin:
        return "UNSURE"

    if top == prob_up:
        return "UP"
    if top == prob_down:
        return "DOWN"
    return "UNSURE"


def detect_market_phase(last_row: pd.Series) -> str:
    if (
        last_row["ema_9"] > last_row["ema_21"] > last_row["ema_50"]
        and last_row["ema_spread_9_21"] > 0
    ):
        return "bullish"

    if (
        last_row["ema_9"] < last_row["ema_21"] < last_row["ema_50"]
        and last_row["ema_spread_9_21"] < 0
    ):
        return "bearish"

    return "sideways"


def detect_volatility_regime(last_row: pd.Series) -> str:
    if last_row["volatility_10"] > last_row["volatility_20"] * 1.2:
        return "high"
    if last_row["volatility_10"] < last_row["volatility_20"] * 0.8:
        return "low"
    return "normal"


def detect_momentum_state(last_row: pd.Series) -> str:
    rsi = last_row["rsi_14"]
    if rsi >= 60:
        return "positive"
    if rsi <= 40:
        return "negative"
    return "neutral"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def _validate_artifacts(artifacts_dir: Path) -> None:
    required_paths = [
        artifacts_dir / "feature_columns.json",
        artifacts_dir / "model_meta.json",
        artifacts_dir / "training_config.json",
        artifacts_dir / "decision_config.json",
    ]
    missing = [path.name for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required artifacts: {', '.join(missing)}")

    model_path = artifacts_dir / "model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(
            f"Missing required model artifact: {model_path}. Export the trained model as model.pkl."
        )


def _build_model_input(features_df: pd.DataFrame, feature_columns: list[str]) -> tuple[pd.Series, pd.DataFrame]:
    if features_df.empty:
        raise ValueError("Feature frame is empty after preprocessing. Check lookback size and input OHLCV data.")

    missing_columns = [column for column in feature_columns if column not in features_df.columns]
    if missing_columns:
        raise ValueError(f"Missing feature columns required by model: {', '.join(missing_columns)}")

    last_row = features_df.iloc[-1].copy()
    x_last = pd.DataFrame([last_row[feature_columns].to_dict()], columns=feature_columns)
    return last_row, x_last


def predict_latest_forecast(
    df: pd.DataFrame,
    artifacts_dir: Path,
    decision_margin_override: float | None = None,
) -> dict[str, Any]:
    _validate_artifacts(artifacts_dir)
    feature_columns = _load_json(artifacts_dir / "feature_columns.json")
    model_meta = _load_json(artifacts_dir / "model_meta.json")
    training_config = _load_json(artifacts_dir / "training_config.json")
    decision_config = _load_json(artifacts_dir / "decision_config.json")

    if not isinstance(feature_columns, list) or not feature_columns:
        raise ValueError("feature_columns.json must contain a non-empty JSON array.")

    model_path = artifacts_dir / "model.pkl"
    try:
        model = joblib.load(model_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Model artifact not found: {model_path}") from None

    features_df = build_features(df)
    last_row, x_last = _build_model_input(features_df, feature_columns)
    probs = model.predict_proba(x_last)[0]

    prob_down = float(probs[0])
    prob_unsure = float(probs[1])
    prob_up = float(probs[2])

    margin = (
        decision_margin_override
        if decision_margin_override is not None
        else float(decision_config.get("decision_margin", training_config["decision_margin"]))
    )

    decision = apply_decision_layer(
        prob_down=prob_down,
        prob_unsure=prob_unsure,
        prob_up=prob_up,
        margin=margin,
    )

    confidence = float(max(probs) - sorted(probs)[-2])

    return {
        "forecast_time": datetime.now(timezone.utc).isoformat(),
        "symbol": model_meta["symbol"],
        "timeframe": model_meta["timeframe"],
        "prob_up": prob_up,
        "prob_down": prob_down,
        "prob_unsure": prob_unsure,
        "decision": decision,
        "confidence": confidence,
        "market_phase": detect_market_phase(last_row),
        "volatility_regime": detect_volatility_regime(last_row),
        "momentum_state": detect_momentum_state(last_row),
        "model_version": model_meta["model_version"],
        "latest_close": float(df["close"].iloc[-1]),
        "last_candle_time": df.index[-1].isoformat(),
        "feature_count": len(feature_columns),
    }
