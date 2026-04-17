<div align="center">
  <h1>RSI Reversion</h1>
</div>

`rsi_reversion` — mean reversion стратегия, построенная на возврате RSI из зон перепроданности и перекупленности.

<div align="center">
  <h2>Логика</h2>
</div>

- `entry_long`: RSI возвращается выше уровня `oversold`
- `exit_long`: RSI пересекает вверх `exit_mid` или достигает зоны `overbought`
- `entry_short`: опциональная зеркальная логика при возврате RSI ниже `overbought`
- `exit_short`: опциональная зеркальная логика при пересечении вниз `exit_mid` или достижении `oversold`

Сигналы рассчитываются только по текущему и предыдущему барам.

<div align="center">
  <h2>Параметры</h2>
</div>

| Параметр | Описание |
| --- | --- |
| `rsi_period` | Период сглаживания RSI. |
| `oversold` | Уровень перепроданности для long-входа. |
| `overbought` | Уровень перекупленности для short-входа. |
| `exit_mid` | Средний уровень для выхода из позиции. |
| `allow_short` | Включает short-логику. |

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
- `rsi`

<div align="center">
  <h2>Пример Использования</h2>
</div>

```python
from shared.registry import StrategyRegistry

registry = StrategyRegistry()
strategy = registry.create(
    "rsi_reversion",
    {"rsi_period": 10, "oversold": 25.0, "overbought": 75.0, "exit_mid": 50.0},
)
result = strategy.run(df)
```

<div align="center">
  <h2>Ограничения</h2>
</div>

- В сильном тренде RSI может долго оставаться в экстремальной зоне.
- Параметры должны удовлетворять условию `oversold < exit_mid < overbought`.
