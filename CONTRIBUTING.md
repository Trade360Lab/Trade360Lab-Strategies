# Contributing

## Development Setup

Use Python 3.11+.

Recommended setup:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## Repository Layout

- `strategies/`: strategy implementations grouped by category
- `indicators/`: reusable indicator functions
- `shared/`: contracts, validation, registry, and common helpers
- `examples/`: example configuration payloads
- `tests/`: unit and integration coverage

## Adding a New Strategy

1. Create a directory under the correct category inside `strategies/`.
2. Use a lowercase snake_case slug for the folder name.
3. Add `strategy.py` with a `BaseStrategy` subclass.
4. Add `manifest.json` that fully describes the strategy.
5. Add `README.md` with strategy-specific documentation.
6. Add strategy tests under the local `tests/` directory.
7. Add an example config under `examples/` if the strategy is meant to be user-facing.

## Slug Rules

- Use lowercase snake_case.
- Keep the slug short and descriptive.
- The slug must be globally unique.
- The strategy directory name must match the slug.

Examples:
- `ema_cross`
- `rsi_reversion`
- `donchian_breakout`

## Manifest Checklist

Each manifest must declare:
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

Every parameter should include a meaningful `description` and a realistic default.

## Required Tests

For every new strategy:
- smoke test
- schema test
- determinism test
- invalid params test
- no-lookahead sanity test

For shared infrastructure changes:
- update or add unit tests for affected helpers
- add integration coverage when registry or discovery behavior changes

## Running Quality Checks

Run lint:

```bash
.venv/bin/ruff check .
```

Run tests:

```bash
.venv/bin/python -m pytest
```

## Commit Message Rules

Use atomic commits with these patterns:

- `chore(core): ...`
- `chore(registry): ...`
- `chore(validation): ...`
- `chore(indicators): ...`
- `chore(ci): ...`
- `chore(docs): ...`
- `chore(readme): ...`
- `test(...): ...`
- `refactor(...): ...`
- `feat(<strategy_slug>): ...`

Important rule:
- each new strategy must be a separate commit using `feat(<strategy_slug>): ...`

Do not:
- combine multiple strategies in one commit
- use vague messages like `update files`
- mix unrelated refactors into strategy feature commits

