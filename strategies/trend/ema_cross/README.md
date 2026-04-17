# EMA Crossover

`ema_cross` is a trend-following strategy based on a fast and slow exponential moving average.

## Logic

- `entry_long`: fast EMA crosses above slow EMA.
- `exit_long`: fast EMA crosses below slow EMA.
- `entry_short`: optional mirror of `exit_long`.
- `exit_short`: optional mirror of `entry_long`.

The strategy only compares the current bar to the previous bar, so it does not use future values.

## Parameters

| Name | Description |
| --- | --- |
| `fast_period` | Fast EMA lookback period. |
| `slow_period` | Slow EMA lookback period. |
| `allow_short` | Enables symmetric short signals. |

## Required Columns

- `open`
- `high`
- `low`
- `close`
- `volume`

Input data must use a datetime index or a datetime `timestamp` column.

## Output Columns

- `entry_long`
- `entry_short`
- `exit_long`
- `exit_short`
- `ema_fast`
- `ema_slow`

## Example

```python
from shared.registry import StrategyRegistry

registry = StrategyRegistry()
strategy = registry.create("ema_cross", {"fast_period": 10, "slow_period": 30})
result = strategy.run(df)
```

## Caveats

- Flat or choppy markets can generate frequent whipsaws.
- `fast_period` must stay below `slow_period`.
