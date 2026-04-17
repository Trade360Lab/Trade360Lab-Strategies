<div align="center">
  <h1>EMA Crossover</h1>
</div>

`ema_cross` — трендовая стратегия на пересечении быстрой и медленной экспоненциальных скользящих средних.

<div align="center">
  <h2>Логика</h2>
</div>

- `entry_long`: быстрая EMA пересекает медленную снизу вверх
- `exit_long`: быстрая EMA пересекает медленную сверху вниз
- `entry_short`: опциональное зеркальное поведение для `exit_long`
- `exit_short`: опциональное зеркальное поведение для `entry_long`

Стратегия использует только текущий и предыдущий бар, поэтому будущие значения не используются.

<div align="center">
  <h2>Параметры</h2>
</div>

| Параметр | Описание |
| --- | --- |
| `fast_period` | Период быстрой EMA. |
| `slow_period` | Период медленной EMA. |
| `allow_short` | Включает симметричные short-сигналы. |

<div align="center">
  <h2>Обязательные Колонки</h2>
</div>

- `open`
- `high`
- `low`
- `close`
- `volume`

Входные данные должны использовать datetime index или datetime колонку `timestamp`.

<div align="center">
  <h2>Выходные Колонки</h2>
</div>

- `entry_long`
- `entry_short`
- `exit_long`
- `exit_short`
- `ema_fast`
- `ema_slow`

<div align="center">
  <h2>Пример Использования</h2>
</div>

```python
from shared.registry import StrategyRegistry

registry = StrategyRegistry()
strategy = registry.create("ema_cross", {"fast_period": 10, "slow_period": 30})
result = strategy.run(df)
```

<div align="center">
  <h2>Ограничения</h2>
</div>

- Во флэте стратегия может давать много ложных пересечений.
- `fast_period` должен быть меньше `slow_period`.
