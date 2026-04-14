# RSIChaikBot

**RSIChaikBot** — minimal production-like runtime-каркас для long-only стратегии `MACD + RSI reclaim` на закрытых свечах.

Проект не заменяет исследовательский notebook и не пытается быть готовой live-trading системой. Его задача — вынести торговую идею в отдельную runtime-архитектуру с разделением на strategy, market polling, execution и persistence.

Имя проекта сохранено прежним, но текущая версия исследовательской логики в `Strategy.ipynb` уже не использует Chaikin-подтверждение.

## Что это за бот

Бот работает по закрытой свече и делает следующее:

- загружает и обновляет буфер market data
- ждёт только новые closed candles
- считает структурированный `Signal`, а не `bool`
- рассчитывает размер позиции через `risk_per_trade`
- передаёт ордерное намерение в execution layer
- сохраняет локальный state в JSON
- пишет сигналы и сделки в CSV
- может восстанавливаться после рестарта по локальному state

Это именно runtime skeleton: operational layer есть, но exchange-интеграция для live режима пока оставлена как явно обозначенный skeleton.

## Важное предупреждение

Это **не готовая live-trading система**.

Перед любым live использованием обязательно проверить:

- эквивалентность расчётов notebook и runtime-кода
- корректность логики входов и выходов на реальных closed candles
- учёт комиссий, slippage, tick size и lot size для конкретной биржи
- восстановление состояния после падения процесса и перезапуска контейнера
- reconciliation локального `state` с реальным состоянием биржи
- сетевые ошибки, rate limits, таймауты, повторные запросы
- фактический порядок исполнения стопов, тейков и market exits

Paper mode по умолчанию предназначен только для проверки runtime-поведения и журналирования. Он не моделирует весь набор биржевых edge cases.

## Что это за стратегия

Стратегия long-only и строится на комбинации двух сигналов:

1. `MACD` должен быть bullish.
2. `RSI` должен reclaim-нуться вверх через заданный порог.

Выходы поддерживаются в следующем порядке:

1. `stop-loss`
2. `take-profit` по `RR`
3. optional `signal exit` при ухудшении MACD / RSI
4. `timeout` по числу баров

Стоп рассчитывается через `ATR` и `atr_stop_mult`.

Сильные стороны стратегии:

- фильтрация импульса через MACD
- вход не по любому RSI, а по reclaim через уровень
- формализованный риск-менеджмент через `risk_per_trade`

Слабые стороны стратегии:

- чувствительность к задержкам и качеству closed-candle polling
- уязвимость к боковику и резким разворотам после входа
- результат сильно зависит от параметров RSI/MACD и модели исполнения
- локальный state без exchange reconciliation недостаточен для настоящего live режима

## Связь с исследовательским ноутбуком

В корне проекта сохранён `Strategy.ipynb`.

Важно:

- notebook не заменяется runtime-кодом
- runtime сохраняет торговую идею, но оборачивает её в operational architecture
- research и runtime-код физически разделены по разным файлам
- execution, persistence и market polling не смешиваются с strategy logic
- перед live использованием нужно вручную проверить parity между notebook и runtime

Runtime не импортирует notebook напрямую и не пытается исполнять notebook-код в production loop.

## Структура проекта

```text
RSIChaikBot/
├── Strategy.ipynb
├── rsi_chaik_bot/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── market.py
│   ├── strategy.py
│   ├── execution.py
│   ├── storage.py
│   └── utils.py
├── README.md
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── assets/
│   └── placeholder.txt
├── data/
├── logs/
└── state/
```

## Описание файлов

- `rsi_chaik_bot/app.py` — главный entrypoint и runtime loop
- `rsi_chaik_bot/config.py` — единая конфигурация, чтение `.env`, dataclass-style config
- `rsi_chaik_bot/models.py` — модели `Candle`, `Signal`, `PositionState`, `OrderIntent`, `OrderResult`, `BotState`
- `rsi_chaik_bot/market.py` — initial history, polling по закрытым свечам, обновление буфера
- `rsi_chaik_bot/strategy.py` — чистое ядро стратегии без зависимости от execution
- `rsi_chaik_bot/execution.py` — `BaseExecutionClient`, `PaperExecutionClient`, `LiveExecutionClient`
- `rsi_chaik_bot/storage.py` — JSON state recovery, CSV logging сигналов и сделок
- `rsi_chaik_bot/utils.py` — logger, rounding, safe float, time helpers
- `.env.example` — пример переменных окружения
- `Dockerfile` и `docker-compose.yml` — контейнеризация runtime
- `data/` — CSV с сигналами и сделками
- `logs/` — runtime-логи приложения
- `state/` — локальное состояние бота

## Логика стратегии

Runtime-реализация проверяет условия в таком порядке:

1. Прогрев индикаторов.
2. Расчёт `RSI`, `MACD`, `ATR`.
3. Если позиция уже открыта:
   `stop-loss -> take-profit -> signal exit -> timeout`
4. Если позиции нет:
   `MACD bullish -> RSI reclaim`
5. При валидном входе строятся `entry`, `stop`, `take` и риск на единицу.
6. Размер позиции считается в runtime через `risk_per_trade`.

## Quick start / запуск

### Локально

Linux/macOS:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m rsi_chaik_bot.app
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m rsi_chaik_bot.app
```

### Docker

```bash
docker build -t rsi-chaik-bot .
docker compose up --build -d
```

Остановить сервис:

```bash
docker compose down
```

## Environment variables

Основные переменные:

- `PAPER_MODE` — paper или live режим
- `SYMBOL`, `TIMEFRAME` — рынок и таймфрейм
- `HISTORY_LIMIT` — размер буфера свечей
- `INITIAL_CASH`, `FEE_RATE`, `SLIPPAGE_PCT` — execution settings
- `PRICE_STEP`, `QUANTITY_STEP`, `MIN_QUANTITY` — ограничения округления
- `MACD_FAST`, `MACD_SLOW`, `MACD_SIGNAL` — MACD-параметры
- `RSI_PERIOD`, `RSI_ENTRY_LEVEL`, `RSI_EXIT_LEVEL` — RSI-параметры
- `ATR_PERIOD`, `ATR_STOP_MULT` — расчёт stop-loss
- `ENABLE_SIGNAL_EXIT` — включение signal exit
- `RISK_PER_TRADE`, `RR_TARGET`, `MAX_BARS_IN_TRADE` — риск и сопровождение позиции
- `KILL_SWITCH` — глобальная блокировка торговой логики

Полный пример есть в `.env.example`.

## Paper vs Live execution

Сейчас доступны два режима:

- `PaperExecutionClient` — рабочий default для paper runtime
- `LiveExecutionClient` — skeleton / stub для будущей биржевой интеграции

Важно:

- strategy layer не зависит от конкретного execution adapter
- paper mode обновляет cash и позицию локально
- live mode пока не отправляет реальные ордера и не делает exchange sync
- переключение в `PAPER_MODE=false` без дописывания live client не делает проект live-ready

## Что проверить перед live

- точность round-trip между `Signal -> OrderIntent -> OrderResult`
- соответствие локального stop/take фактической биржевой модели исполнения
- состояние после network glitches и частичных сбоев
- синхронизацию open position после рестарта
- обработку частичных fill, отмен, дубликатов и повторных запросов
- мониторинг логов, алерты и kill-switch процедуру
- реальную защиту API-ключей и секретов

Без этих проверок проект следует считать только production-like skeleton для дальнейшего развития.
