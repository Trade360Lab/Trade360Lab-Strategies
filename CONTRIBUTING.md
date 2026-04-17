<div align="center">
  <h1>Правила Участия В Разработке</h1>
</div>

<div align="center">
  <h2>Подготовка Окружения</h2>
</div>

Используйте Python 3.11+.

Рекомендуемый setup:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

<div align="center">
  <h2>Структура Репозитория</h2>
</div>

- `strategies/`: реализации стратегий, сгруппированные по категориям
- `indicators/`: переиспользуемые индикаторы
- `shared/`: контракты, validation, registry и общие helpers
- `examples/`: примеры пользовательских конфигов
- `tests/`: unit и integration тесты

<div align="center">
  <h2>Как Добавить Новую Стратегию</h2>
</div>

1. Создайте директорию в нужной категории внутри `strategies/`.
2. Используйте lowercase snake_case slug для имени каталога.
3. Добавьте `strategy.py` с классом-наследником `BaseStrategy`.
4. Добавьте `manifest.json` с полным описанием стратегии.
5. Добавьте `README.md` с документацией по стратегии.
6. Добавьте локальные тесты в директорию `tests/`.
7. Если стратегия пользовательская, добавьте пример конфига в `examples/`.

<div align="center">
  <h2>Правила Для Slug</h2>
</div>

- используйте lowercase snake_case
- slug должен быть коротким и понятным
- slug должен быть уникальным во всём репозитории
- имя директории стратегии должно совпадать со slug

Примеры:
- `ema_cross`
- `rsi_reversion`
- `donchian_breakout`

<div align="center">
  <h2>Checklist Для Manifest</h2>
</div>

Каждый manifest должен содержать:
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

У каждого параметра должно быть осмысленное `description` и реалистичное `default` значение.

<div align="center">
  <h2>Обязательные Тесты</h2>
</div>

Для каждой новой стратегии:
- smoke test
- schema test
- determinism test
- invalid params test
- no-lookahead sanity test

Для изменений в shared/core:
- обновляйте или добавляйте unit tests для затронутых helpers
- добавляйте integration coverage, если меняется registry или discovery behavior

<div align="center">
  <h2>Запуск Проверок</h2>
</div>

Запуск линтера:

```bash
.venv/bin/ruff check .
```

Запуск тестов:

```bash
.venv/bin/python -m pytest
```

<div align="center">
  <h2>Правила Для Commit Messages</h2>
</div>

Используйте атомарные коммиты с такими шаблонами:

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

Ключевое правило:
- каждая новая стратегия должна попадать в отдельный commit вида `feat(<strategy_slug>): ...`

Нельзя:
- объединять несколько стратегий в один commit
- использовать размытые сообщения вроде `update files`
- смешивать несвязанные refactor-изменения с feature-коммитом стратегии
