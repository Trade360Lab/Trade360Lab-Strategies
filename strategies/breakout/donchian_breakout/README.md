<div align="center">
  <h1>Donchian Breakout</h1>
</div>

`donchian_breakout` — breakout стратегия на пробое предыдущих границ канала Дончиана.

<div align="center">
  <h2>Логика</h2>
</div>

- `entry_long`: цена закрытия пересекает вверх предыдущую верхнюю границу канала
- `exit_long`: цена закрытия пересекает вниз предыдущую midline exit-канала
- `entry_short`: опциональная зеркальная логика при пробое предыдущей нижней границы
- `exit_short`: опциональная зеркальная логика при возврате выше предыдущей exit midline

Для всех триггеров используются сдвинутые значения канала, поэтому текущий бар не сравнивается с каналом, который уже включает его собственные high/low.

<div align="center">
  <h2>Параметры</h2>
</div>

| Параметр | Описание |
| --- | --- |
| `lookback` | Окно Дончиана для входов. |
| `exit_lookback` | Окно Дончиана для расчёта exit midline. |
| `allow_short` | Включает short breakout сигналы. |

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
- `donchian_upper`
- `donchian_lower`
- `donchian_mid`
- `donchian_exit_upper`
- `donchian_exit_lower`
- `donchian_exit_mid`

<div align="center">
  <h2>Пример Использования</h2>
</div>

```python
from shared.registry import StrategyRegistry

registry = StrategyRegistry()
strategy = registry.create(
    "donchian_breakout",
    {"lookback": 55, "exit_lookback": 20, "allow_short": True},
)
result = strategy.run(df)
```

<div align="center">
  <h2>Ограничения</h2>
</div>

- Во время бокового рынка breakout-подход может часто давать ложные входы.
- При больших окнах `lookback` сигналы становятся реже.
