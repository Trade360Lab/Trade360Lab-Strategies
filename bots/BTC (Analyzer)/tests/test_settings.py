from pathlib import Path

from app.settings import load_runtime_settings


def test_env_settings_defaults(monkeypatch, tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    (artifacts_dir / "feature_columns.json").write_text("[\"ret_1\"]", encoding="utf-8")
    (artifacts_dir / "model_meta.json").write_text(
        "{\"symbol\": \"BTCUSDT\", \"timeframe\": \"1h\", \"model_version\": \"v1\"}",
        encoding="utf-8",
    )
    (artifacts_dir / "training_config.json").write_text(
        "{\"expected_freq\": \"1h\", \"lookback_bars\": 500}",
        encoding="utf-8",
    )
    (artifacts_dir / "decision_config.json").write_text(
        "{\"decision_margin\": 0.1, \"telegram_enabled_default\": false, \"report_title\": \"BTC Daily Outlook\", \"use_closed_candle_only\": true}",
        encoding="utf-8",
    )
    (artifacts_dir / "model.pkl").write_bytes(b"placeholder")

    monkeypatch.setenv("ARTIFACTS_DIR", str(artifacts_dir))
    monkeypatch.delenv("BINANCE_SYMBOL", raising=False)
    monkeypatch.delenv("BINANCE_INTERVAL", raising=False)
    monkeypatch.delenv("LOOKBACK_BARS", raising=False)
    monkeypatch.delenv("DECISION_MARGIN", raising=False)
    monkeypatch.delenv("TELEGRAM_ENABLED", raising=False)
    monkeypatch.delenv("REQUEST_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("DRY_RUN", raising=False)
    monkeypatch.delenv("TZ", raising=False)

    settings = load_runtime_settings()

    assert settings.artifacts_dir == artifacts_dir
    assert settings.binance_symbol == "BTCUSDT"
    assert settings.binance_interval == "1h"
    assert settings.lookback_bars == 500
    assert settings.decision_margin == 0.1
    assert settings.telegram_enabled is False
    assert settings.request_timeout_seconds == 20
    assert settings.log_level == "INFO"
    assert settings.dry_run is False
    assert settings.tz == "UTC"
