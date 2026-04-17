# BTC Daily Forecast Bot

Бот ежедневно строит вероятностный прогноз по `BTCUSDT` на основе готовой XGBoost-модели и model artifacts. Он не торгует и не переобучает модель на лету: runtime только загружает свежие свечи Binance, собирает фичи, считает `predict_proba`, применяет decision layer и публикует отчёт.

## Что делает бот

- Загружает OHLCV-свечи Binance через REST `klines`.
- Валидирует структуру данных и шаг по времени.
- Собирает признаки, совместимые с обученной моделью.
- Загружает `artifacts/model.pkl` и runtime-конфиг артефактов.
- Возвращает прогноз с вероятностями `UP / DOWN / UNSURE`.
- Печатает отчёт в stdout.
- Опционально отправляет отчёт в Telegram.
- Сохраняет историю запусков в `logs/forecast_history.jsonl`.

## Структура проекта

```text
.
├── artifacts/
│   ├── decision_config.json
│   ├── feature_columns.json
│   ├── model_meta.json
│   ├── model.pkl
│   └── training_config.json
├── binance_loader.py
├── predictor.py
├── reporter.py
├── run_daily_bot.py
├── run_daily_boy.py
├── settings.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── tests/
```

`run_daily_boy.py` оставлен только как compatibility wrapper. Основной entrypoint: `run_daily_bot.py`.

## Обязательные артефакты

В `artifacts/` должны лежать:

- `model.pkl` — сериализованная модель, совместимая с `joblib.load`.
- `feature_columns.json` — список колонок, которые ожидает модель.
- `model_meta.json` — метаданные модели, включая `symbol`, `timeframe`, `model_version`.
- `training_config.json` — training-related параметры, включая `expected_freq`, `lookback_bars`.
- `decision_config.json` — runtime decision/reporting параметры.

Важно: в текущем runtime валидный `model.pkl` обязателен. Если в папке лежит только legacy `model.json`, бот завершится fail-fast с понятной ошибкой.

## Environment Variables

Поддерживаются такие переменные:

- `ARTIFACTS_DIR=artifacts`
- `TELEGRAM_ENABLED=false`
- `TELEGRAM_BOT_TOKEN=`
- `TELEGRAM_CHAT_ID=`
- `BINANCE_SYMBOL=BTCUSDT`
- `BINANCE_INTERVAL=1h`
- `LOOKBACK_BARS=500`
- `DECISION_MARGIN=0.10`
- `REQUEST_TIMEOUT_SECONDS=20`
- `LOG_LEVEL=INFO`
- `DRY_RUN=false`
- `TZ=UTC`
- `USE_CLOSED_CANDLE_ONLY=true`

Приоритет такой:

1. Значения из environment.
2. Значения из `decision_config.json`, `training_config.json`, `model_meta.json`.
3. Безопасные дефолты runtime.

## Пример `.env`

```env
ARTIFACTS_DIR=artifacts
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
BINANCE_SYMBOL=BTCUSDT
BINANCE_INTERVAL=1h
LOOKBACK_BARS=500
DECISION_MARGIN=0.10
REQUEST_TIMEOUT_SECONDS=20
LOG_LEVEL=INFO
DRY_RUN=false
TZ=UTC
USE_CLOSED_CANDLE_ONLY=true
```

## Локальный запуск

1. Создать виртуальное окружение и установить зависимости:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

2. Подготовить `.env`:

```bash
cp .env.example .env
```

3. Экспортировать переменные перед запуском:

```bash
set -a
. ./.env
set +a
python run_daily_bot.py
```

Если Telegram credentials не заданы или `TELEGRAM_ENABLED=false`, бот не падает и просто пропускает отправку.

## Запуск через Docker

Сборка:

```bash
docker build -t btc-daily-bot .
```

Запуск:

```bash
docker run --rm --env-file .env -v "$(pwd)/artifacts:/app/artifacts:ro" -v "$(pwd)/logs:/app/logs" btc-daily-bot
```

## Запуск через Docker Compose

```bash
cp .env.example .env
docker compose up --build bot
```

## Пример expected output

```text
2026-04-17 08:00:00,000 INFO __main__ Starting BTC analyzer: symbol=BTCUSDT timeframe=1h lookback=500 dry_run=False
2026-04-17 08:00:01,234 INFO __main__ Loading market data from Binance
2026-04-17 08:00:02,345 INFO predictor Loading model artifact from artifacts/model.pkl
============================================================
BTC Daily Outlook

Symbol: BTCUSDT
Timeframe: 1h
Forecast time: 2026-04-17T08:00:02.500000+00:00
Model version: btc_h1_xgb_v1

Probabilities:
- UP: 41.20%
- DOWN: 27.35%
- UNSURE: 31.45%

Decision: UP
Confidence: 9.75%

Market context:
- Phase: bullish
- Volatility: normal
- Momentum: positive
============================================================
```

## Что делать без Telegram credentials

- Оставить `TELEGRAM_ENABLED=false`, и бот будет работать только в stdout + `logs/forecast_history.jsonl`.
- Или оставить `TELEGRAM_ENABLED=true`, но без `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`; тогда отправка будет пропущена с warning в логах.

## Как обновить модельные артефакты

1. Экспортировать новую обученную модель в `artifacts/model.pkl`.
2. Обновить `artifacts/feature_columns.json`, если поменялся feature set.
3. Обновить `artifacts/model_meta.json` с новой `model_version`.
4. При необходимости обновить `training_config.json`.
5. При необходимости обновить `decision_config.json` для runtime decision/reporting параметров.

После этого можно перезапустить бот без изменения кода.
