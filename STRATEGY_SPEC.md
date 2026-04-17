# Strategy Library Specification

## Purpose

This repository contains a manifest-driven library of trading strategies for Trade360Lab. The library is designed to support backtesting, optimization, and future live-trading integrations without coupling strategy logic to a specific execution engine.

## Strategy Contract

Every strategy must inherit from `shared.base_strategy.BaseStrategy`.

Required class attributes:
- `slug`
- `name`
- `category`
- `default_params`

Required methods:
- `validate_params()`
- `compute_indicators(df)`
- `generate_signals(df)`

Runtime flow:
1. `run(df)` performs a defensive copy of the input dataframe.
2. Input schema validation runs before any indicator computation.
3. `compute_indicators(df)` adds derived columns.
4. `generate_signals(df)` populates the standard signal columns.
5. Output schema validation guarantees required signal columns exist and are boolean-like.

## Input Schema

Required OHLCV columns:
- `open`
- `high`
- `low`
- `close`
- `volume`

Time axis requirements:
- Input must have either a datetime index or a datetime `timestamp` column.
- The time axis must be sorted ascending.
- Duplicate timestamps are not allowed.
- Empty dataframes are invalid.

## Output Schema

Required signal columns:
- `entry_long`
- `entry_short`
- `exit_long`
- `exit_short`

Optional columns:
- `stop_loss`
- `take_profit`
- `signal_score`
- `regime`
- any indicator columns used by the strategy

Signal columns must be boolean or safely coercible to boolean.

## Naming Conventions

General rules:
- Strategy slug: lowercase snake_case.
- Manifest `class_name`: PascalCase and must match the class in `strategy.py`.
- Strategy directories: match the slug exactly.
- Indicator column names: short, descriptive, deterministic.

Examples:
- `ema_fast`
- `ema_slow`
- `rsi`
- `donchian_upper`
- `donchian_lower`
- `donchian_mid`

## Parameter Rules

All user-facing parameters must be declared in `manifest.json`.

Each parameter definition must include:
- `type`
- `default`
- `description`

Use these fields when applicable:
- `min`
- `max`
- `step`
- `options`
- `optimize`

Strategy implementations may enforce stricter semantic checks than the manifest alone. For example, `fast_period < slow_period`.

## Manifest Rules

Each strategy directory must include `manifest.json`.

Required manifest fields:
- `slug`
- `name`
- `category`
- `version`
- `description`
- `direction`
- `class_name`
- `timeframes`
- `symbols`
- `required_columns`
- `outputs`
- `parameters`

Manifest expectations:
- `slug` must be unique across the repository.
- `direction` may contain `long`, `short`, or both.
- `required_columns` must include the OHLCV base schema.
- `outputs` must include the four required signal columns.
- `class_name` must point to a class defined in `strategy.py`.

`shared.registry.StrategyRegistry` treats the manifest as the source of truth for discovery and instantiation.

## Lookahead Bias Policy

Lookahead bias is forbidden.

Allowed:
- comparisons to prior bars via `shift(1)` or larger positive shifts
- rolling calculations that only use current and past bars

Forbidden:
- `shift(-1)` or any future-bar access for current-bar signal generation
- comparisons against indicator values that already include future data
- hidden post-processing that mutates historical signals using later observations

## Rules for New Strategies

Each strategy must include:
- `strategy.py`
- `manifest.json`
- `README.md`
- `tests/`

Each strategy must:
- inherit from `BaseStrategy`
- validate its parameters explicitly
- document required columns and output columns
- use reusable indicators or shared helpers when possible
- avoid duplicating cross/signal logic that belongs in `shared/` or `indicators/`

## Testing Requirements

Every strategy must have tests covering:
- smoke execution on fixture OHLCV data
- required output schema
- deterministic repeated runs
- invalid params with clear errors
- basic no-lookahead sanity

Core infrastructure must have tests for:
- indicators
- signal helpers
- manifest validation
- registry discovery and instantiation
- base strategy behavior

