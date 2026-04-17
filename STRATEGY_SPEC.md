<div align="center">
  <h1>Спецификация Библиотеки Стратегий</h1>
</div>

<div align="center">
  <h2>Назначение</h2>
</div>

Этот репозиторий содержит manifest-driven библиотеку торговых стратегий для Trade360Lab. Библиотека должна поддерживать бэктестинг, оптимизацию и дальнейшую интеграцию в live-режим без жёсткой привязки к конкретному движку исполнения.

<div align="center">
  <h2>Контракт Стратегии</h2>
</div>

Каждая стратегия обязана наследоваться от `shared.base_strategy.BaseStrategy`.

Обязательные class attributes:
- `slug`
- `name`
- `category`
- `default_params`

Обязательные методы:
- `validate_params()`
- `compute_indicators(df)`
- `generate_signals(df)`

Порядок выполнения:
1. `run(df)` делает defensive copy входного DataFrame.
2. До расчёта индикаторов выполняется валидация входной схемы.
3. `compute_indicators(df)` добавляет производные колонки.
4. `generate_signals(df)` заполняет стандартные сигнальные колонки.
5. Валидация выхода проверяет наличие обязательных сигналов и их корректный булев тип.

<div align="center">
  <h2>Входная Схема</h2>
</div>

Обязательные OHLCV колонки:
- `open`
- `high`
- `low`
- `close`
- `volume`

Требования ко времени:
- на входе должен быть либо datetime index, либо datetime колонка `timestamp`
- временная ось должна быть отсортирована по возрастанию
- дублирующиеся timestamps запрещены
- пустые DataFrame запрещены

<div align="center">
  <h2>Выходная Схема</h2>
</div>

Обязательные сигнальные колонки:
- `entry_long`
- `entry_short`
- `exit_long`
- `exit_short`

Опциональные колонки:
- `stop_loss`
- `take_profit`
- `signal_score`
- `regime`
- любые индикаторные колонки, которые рассчитывает стратегия

Сигнальные колонки должны быть булевыми или безопасно приводимыми к булевому типу.

<div align="center">
  <h2>Соглашения По Именованию</h2>
</div>

Общие правила:
- `slug` стратегии: lowercase snake_case
- `class_name` в manifest: PascalCase и должен совпадать с классом в `strategy.py`
- директория стратегии должна точно совпадать со `slug`
- имена индикаторных колонок должны быть короткими, предсказуемыми и стабильными

Примеры:
- `ema_fast`
- `ema_slow`
- `rsi`
- `donchian_upper`
- `donchian_lower`
- `donchian_mid`

<div align="center">
  <h2>Правила Для Параметров</h2>
</div>

Все пользовательские параметры должны быть объявлены в `manifest.json`.

Каждый параметр обязан содержать:
- `type`
- `default`
- `description`

Дополнительные поля при необходимости:
- `min`
- `max`
- `step`
- `options`
- `optimize`

Реализация стратегии может накладывать более строгие семантические ограничения, чем сам manifest. Например, `fast_period < slow_period`.

<div align="center">
  <h2>Правила Для Manifest</h2>
</div>

Каждая стратегия обязана содержать `manifest.json`.

Обязательные поля manifest:
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

Ожидания от manifest:
- `slug` должен быть уникальным по всему репозиторию
- `direction` может содержать `long`, `short` или оба варианта
- `required_columns` должен включать базовую OHLCV схему
- `outputs` должен включать четыре обязательные сигнальные колонки
- `class_name` должен указывать на класс из `strategy.py`

`shared.registry.StrategyRegistry` использует manifest как источник правды для discovery и instantiation.

<div align="center">
  <h2>Политика Lookahead Bias</h2>
</div>

Lookahead bias запрещён.

Разрешено:
- сравнение с прошлыми барами через `shift(1)` и другие положительные сдвиги
- rolling calculations, использующие только текущие и прошлые бары

Запрещено:
- `shift(-1)` и любой доступ к будущим барам при генерации текущего сигнала
- сравнение с индикатором, который уже включает будущие значения
- скрытая постобработка, изменяющая исторические сигналы на основе более поздних наблюдений

<div align="center">
  <h2>Правила Для Новых Стратегий</h2>
</div>

Каждая стратегия обязана содержать:
- `strategy.py`
- `manifest.json`
- `README.md`
- `tests/`

Каждая стратегия должна:
- наследоваться от `BaseStrategy`
- явно валидировать параметры
- документировать required columns и output columns
- переиспользовать общие индикаторы и helpers, когда это возможно
- не дублировать signal/cross логику, которая уже должна жить в `shared/` или `indicators/`

<div align="center">
  <h2>Требования К Тестам</h2>
</div>

Для каждой стратегии обязательны тесты на:
- smoke execution на fixture OHLCV data
- наличие обязательной выходной схемы
- детерминированность повторного запуска
- понятные ошибки на невалидных параметрах
- базовую sanity-проверку на отсутствие lookahead

Для core-инфраструктуры обязательны тесты на:
- индикаторы
- signal helpers
- manifest validation
- registry discovery и instantiation
- базовое поведение `BaseStrategy`
