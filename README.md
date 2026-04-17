# Trade360Lab Strategies

Manifest-driven library of trading strategies for Trade360Lab. The repository provides a strict strategy contract, reusable indicators, automatic strategy discovery, example configs, and a testable path toward backtest, optimizer, and live-bot integration.

## What is Included

- `shared/`: base strategy contract, dataframe validation, manifest schema, params helpers, signal helpers, and registry
- `indicators/`: reusable pandas-based technical indicators
- `strategies/`: production-oriented strategies grouped by category
- `examples/`: example JSON payloads for launching strategies
- `tests/`: unit and integration coverage
- `STRATEGY_SPEC.md`: library contract and design rules
- `CONTRIBUTING.md`: workflow for adding new strategies

## Project Structure

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

## Installation

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## Running Checks

Run tests:

```bash
.venv/bin/python -m pytest
```

Run lint:

```bash
.venv/bin/ruff check .
```

## Using the Registry

Discover strategies:

```python
from shared.registry import StrategyRegistry

registry = StrategyRegistry()
print(registry.list_strategies())
```

Create a strategy instance by slug:

```python
from shared.registry import StrategyRegistry

registry = StrategyRegistry()
strategy = registry.create("ema_cross", {"fast_period": 12, "slow_period": 26})
result = strategy.run(df)
```

Get manifest metadata:

```python
manifest = registry.get_manifest("rsi_reversion")
search_space = registry.get_manifest("donchian_breakout")["parameters"]
```

## Available Strategies

- `ema_cross`: EMA crossover trend-following strategy with optional short support
- `rsi_reversion`: RSI-based mean-reversion strategy using recovery from oversold or overbought zones
- `donchian_breakout`: breakout strategy based on prior Donchian channel boundaries

## Contract Summary

All strategies:
- inherit from `shared.base_strategy.BaseStrategy`
- accept `params` at initialization
- validate OHLCV input schema
- return the required signal columns
- avoid lookahead bias
- are discovered automatically from `strategies/**/manifest.json`

Required signal columns:
- `entry_long`
- `entry_short`
- `exit_long`
- `exit_short`

See `STRATEGY_SPEC.md` for the full contract.

## Strategy Directory Layout

```text
strategies/<category>/<slug>/
├─ strategy.py
├─ manifest.json
├─ README.md
└─ tests/
```

## Notes

This repository keeps strategy logic separate from execution-engine concerns. The current scope is a clean, extensible strategy library that downstream backtest and live-trading components can consume through a stable contract.
