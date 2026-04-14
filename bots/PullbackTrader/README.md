# PullbackTrader

![PullbackTrader](assets/logo.svg)

## О проекте

**PullbackTrader** — это minimal production-like runtime-каркас для real-time торговли по стратегии **Trend + Pullback** на `BTCUSDT 5m`.

Проект не заменяет исследовательский notebook и не предназначен для бэктестинга. Его задача — перенести уже существующую notebook-логику в понятную runtime-архитектуру, которую потом можно подключать к paper execution и далее к live execution.

## Что это за бот

Бот работает по закрытой свече и делает следующее:

- получает и обновляет market data
- поддерживает буфер свечей
- считает signal структуры, а не просто `bool`
- рассчитывает размер позиции по `risk_per_trade`
- передаёт ордерные команды в execution layer
- хранит state в JSON
- пишет сигналы и сделки в CSV

## Важное предупреждение

Это **runtime skeleton**, а не готовая live-trading система.

Перед live trading обязательно проверить:

- эквивалентность расчётов notebook/runtime
- модель исполнения ордеров и фактические fill prices
- комиссии, slippage, tick size и lot size
- восстановление после рестарта
- reconciliation локального состояния с exchange state

## Что это за стратегия

**Trend + Pullback** — это вход по направлению уже существующего восходящего движения, но не в момент перегретого импульса, а после контролируемого отката.

Почему стратегия не ловит дно и не гонится за ценой:

- она не покупает только из-за падения
- она не входит в любой сильный зелёный бар
- ей нужен уже подтверждённый тренд и затем откат

Почему используются фильтры тренда, волатильности и объёма:

- тренд-фильтр отсеивает сделки против доминирующего движения
- ATR-фильтр исключает слишком вялые и слишком хаотичные режимы
- volume ratio фильтр добавляет требование по рыночной активности

В чём смысл breakout trigger:

- после pullback стратегия ждёт признак возобновления импульса
- для этого используется пробой `micro high`
- это снижает число преждевременных входов внутри незавершённого отката

Сильные стороны стратегии:

- работа по направлению тренда
- отсутствие попыток ловить разворот с нуля
- формализованный risk management

Слабые стороны стратегии:

- возможны пропуски быстрых разворотов
- боковик ухудшает качество сигналов
- результат чувствителен к исполнению и параметрам фильтров

## Связь с исследовательским ноутбуком

В каталоге проекта сохранён `Strategy.ipynb`.

Важно:

- production-реализация сохраняет ту же логику, что и research/backtest notebook
- runtime-код является адаптацией notebook-логики под real-time исполнение
- notebook не переписывается и не заменяется этим проектом
- все изменения касаются архитектуры и operational concerns, а не торговой идеи

Смысл логики не изменён:

- long-only модель
- trend filter: `close > EMA slow` и `EMA slow slope > 0`
- pullback от локального high
- фильтр расстояния до fast EMA
- ATR filter
- volume ratio filter
- breakout trigger по `micro high`
- stop-loss
- take-profit по `RR`
- timeout по количеству баров
- sizing через `risk_per_trade`

## Структура проекта

```text
PullbackTrader/
├── Strategy.ipynb
├── pullback_trader/
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
│   └── logo.svg
├── data/
├── logs/
└── state/
```

## Описание файлов

- `pullback_trader/app.py` — главный entrypoint и runtime loop
- `pullback_trader/config.py` — единая конфигурация и чтение `.env`
- `pullback_trader/models.py` — модели `Candle`, `Signal`, `PositionState`, `OrderResult`, `BotState`
- `pullback_trader/market.py` — initial history, closed-candle polling, обновление буфера
- `pullback_trader/strategy.py` — ядро стратегии без зависимости от execution layer
- `pullback_trader/execution.py` — `BaseExecutionClient`, `PaperExecutionClient`, `LiveExecutionClient`
- `pullback_trader/storage.py` — JSON state и CSV логи
- `pullback_trader/utils.py` — logger, safe float, rounding, time helpers

## Логика стратегии

Runtime-реализация сохраняет порядок проверок из notebook:

1. Тренд-фильтр:
   - `close > ema_slow`
   - `ema_slow_slope > 0`

2. Pullback:
   - рассчитывается откат от предыдущего локального high на окне `swing_window`
   - откат должен быть в диапазоне `pullback_min_pct .. pullback_max_pct`
   - сохраняется условие по расстоянию до `ema_fast` в том же виде, что и в notebook

3. Фильтры:
   - `ATR / close` должен быть в диапазоне `min_atr_pct .. max_atr_pct`
   - `volume / SMA(volume)` должен быть не ниже `min_volume_ratio`

4. Trigger:
   - если `use_breakout_trigger=true`, нужен `close > micro_high`
   - иначе используется альтернативный trigger через `ema_fast`, как в notebook

5. Выход:
   - сначала `stop-loss`
   - затем `take-profit`
   - затем `timeout`

## Расшифровка параметров стратегии

- `ema_fast` — период быстрой EMA
- `ema_slow` — период медленной EMA, определяющей основной тренд
- `atr_period` — период ATR
- `volume_window` — окно SMA для расчёта volume ratio
- `swing_window` — окно для локального high/low
- `slope_lookback` — сколько баров назад используется для оценки slope медленной EMA
- `pullback_min_pct` — минимальный допустимый откат от локального high
- `pullback_max_pct` — максимальный допустимый откат от локального high
- `max_close_above_fast_ema_pct` — параметр условия расстояния до fast EMA, перенесённый без смены смысла
- `min_volume_ratio` — минимальное значение `volume / SMA(volume)`
- `min_atr_pct` — нижняя граница `ATR / close`
- `max_atr_pct` — верхняя граница `ATR / close`
- `use_breakout_trigger` — использовать ли breakout по `micro high`
- `risk_per_trade` — доля свободного cash, которую допускается рискнуть в одной сделке
- `rr_target` — множитель Risk/Reward для take-profit
- `atr_stop_mult` — множитель ATR для ATR-based stop
- `max_bars_in_trade` — максимальное количество баров в позиции

## Как запускается проект

### Локально

Linux/macOS:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m pullback_trader.app
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m pullback_trader.app
```

## Как работает runtime loop

`pullback_trader/app.py` делает следующее:

1. Загружает конфиг и локальный state
2. Загружает history buffer для прогрева индикаторов
3. Если бот перезапущен, пытается обработать пропущенные закрытые свечи
4. Ждёт следующую закрытую свечу
5. Обновляет буфер
6. Вызывает `strategy.evaluate(...)`
7. На entry считает quantity по той же risk logic, что и в notebook
8. Отправляет сигнал в execution client
9. Сохраняет `state/bot_state.json`
10. Пишет сигналы и сделки в CSV

## Где paper mode, где live mode

Сейчас доступны два execution-режима:

- `PaperExecutionClient` — рабочий paper mode
- `LiveExecutionClient` — skeleton для будущей интеграции с биржей

Переключение:

```env
PAPER_MODE=true
```

При этом `pullback_trader/strategy.py` не зависит от конкретного execution adapter.

## Как хранится состояние

Локальное состояние хранится в:

- `state/bot_state.json`

В state сохраняются:

- последняя обработанная свеча
- локальный cash
- текущая позиция
- timestamps последней синхронизации и ордера
- флаги `kill_switch` и `recovery_required`

Важно: в будущем при live execution exchange state должен быть приоритетнее локального state. Для этого оставлен метод `sync_state()`.

## Как логируются сигналы и сделки

- `data/signals.csv` — сигналы стратегии на закрытых свечах
- `data/trades.csv` — факты исполнения ордеров
- `logs/pullback_trader.log` — runtime лог приложения

Это нужно для:

- проверки paper trading
- сверки поведения с notebook
- разбора ошибок и рестартов

## Запуск через Docker

Собрать образ:

```bash
docker build -t pullback-trader .
```

Запустить через Docker Compose:

```bash
docker compose up --build -d
```

Где будут логи и состояние:

- `./logs`
- `./state`
- `./data`

Остановить сервис:

```bash
docker compose down
```

## Recovery и kill switch

В проекте есть базовые места для operational control:

- recovery пропущенных свечей после рестарта
- `kill_switch`, который позволяет держать runtime включённым без торговли
- `last_error` в state для быстрой диагностики

## Roadmap

- добавить реальную интеграцию в `LiveExecutionClient`
- добавить полноценный exchange reconciliation
- подтянуть symbol filters и exchange metadata
- добавить алерты и healthcheck
- добавить unit-тесты на эквивалентность notebook/runtime
- расширить risk controls для paper/live mode

## Итог

Этот проект сохраняет торговую модель из notebook и переводит её в аккуратный runtime-каркас для дальнейшего paper/live execution без переписывания торговой идеи.
