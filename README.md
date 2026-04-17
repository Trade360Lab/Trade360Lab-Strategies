<p align="center">
  <img src="./public/BlueLogo.png" alt="Trade360Lab Logo" width="600" />
</p>

<div align="center">
  <h1>Trade360Lab Strategies</h1>
</div>

Библиотека торговых стратегий для Trade360Lab с manifest-driven архитектурой. Репозиторий содержит единый контракт стратегии, переиспользуемые индикаторы, автоматический registry, примеры конфигов и тестовую базу для дальнейшей интеграции в backtest, optimizer и live-bot.

<div align="center">
  <h2>Что Входит В Репозиторий</h2>
</div>

- `shared/`: базовый контракт стратегии, валидация DataFrame, schema/manifest helpers, registry и общие signal helpers
- `indicators/`: переиспользуемые технические индикаторы на `pandas`
- `strategies/`: стратегии, сгруппированные по категориям
- `examples/`: примеры JSON-конфигов для запуска стратегий
- `tests/`: unit и integration тесты
- `STRATEGY_SPEC.md`: спецификация библиотеки и контрактов
- `CONTRIBUTING.md`: правила добавления новых стратегий и разработки

<div align="center">
  <h2>Структура Проекта</h2>
</div>

```text
.
├─ strategies/
│  ├─ trend/
│  │  └─ ema_cross/
│  ├─ mean_reversion/
│  │  └─ rsi_reversion/
│  └─ breakout/
│     └─ donchian_breakout/
├─ indicators/
│  ├─ trend/
│  ├─ momentum/
│  ├─ volatility/
│  └─ volume/
├─ shared/
├─ examples/
├─ tests/
│  ├─ fixtures/
│  ├─ unit/
│  └─ integration/
├─ STRATEGY_SPEC.md
├─ CONTRIBUTING.md
├─ README.md
└─ pyproject.toml
```

<div align="center">
  <h2>Установка</h2>
</div>

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

<div align="center">
  <h2>Проверки Качества</h2>
</div>

Запуск тестов:

```bash
.venv/bin/python -m pytest
```

Запуск линтера:

```bash
.venv/bin/ruff check .
```

<div align="center">
  <h2>Использование Registry</h2>
</div>

Получить список доступных стратегий:

```python
from shared.registry import StrategyRegistry

registry = StrategyRegistry()
print(registry.list_strategies())
```

Создать экземпляр стратегии по `slug`:

```python
from shared.registry import StrategyRegistry

registry = StrategyRegistry()
strategy = registry.create("ema_cross", {"fast_period": 12, "slow_period": 26})
result = strategy.run(df)
```

Получить manifest стратегии:

```python
manifest = registry.get_manifest("rsi_reversion")
search_space = registry.get_manifest("donchian_breakout")["parameters"]
```

<div align="center">
  <h2>Доступные Стратегии</h2>
</div>

- `ema_cross`: трендовая стратегия на пересечении быстрых и медленных EMA
- `rsi_reversion`: mean reversion стратегия на возврате RSI из зон перепроданности и перекупленности
- `donchian_breakout`: breakout стратегия на пробое предыдущих границ канала Дончиана

<div align="center">
  <h2>Кратко О Контракте</h2>
</div>

Все стратегии:
- наследуются от `shared.base_strategy.BaseStrategy`
- принимают `params` при инициализации
- валидируют входной OHLCV DataFrame
- возвращают обязательные сигнальные колонки
- не используют lookahead bias
- автоматически обнаруживаются через `strategies/**/manifest.json`

Обязательные сигнальные колонки:
- `entry_long`
- `entry_short`
- `exit_long`
- `exit_short`

Полный контракт описан в `STRATEGY_SPEC.md`.

<div align="center">
  <h2>Структура Каталога Стратегии</h2>
</div>

```text
strategies/<category>/<slug>/
├─ strategy.py
├─ manifest.json
├─ README.md
└─ tests/
```

<div align="center">
  <h2>Примечание</h2>
</div>

Репозиторий хранит только библиотечный слой стратегий и не смешивает его с логикой исполнения ордеров. Это облегчает дальнейшее подключение стратегий к отдельным backtest и live runtime компонентам.
