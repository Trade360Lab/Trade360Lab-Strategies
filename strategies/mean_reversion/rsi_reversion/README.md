# RSI Reversion

`rsi_reversion` is a mean-reversion strategy built around RSI recovering from oversold or overbought extremes.

## Logic

- `entry_long`: RSI crosses back above the `oversold` threshold.
- `exit_long`: RSI crosses above `exit_mid` or reaches the `overbought` threshold.
- `entry_short`: optional mirror logic when RSI crosses back below `overbought`.
- `exit_short`: optional mirror logic when RSI crosses below `exit_mid` or reaches `oversold`.

Signals are based only on current and previous bars.

## Parameters

| Name | Description |
| --- | --- |
| `rsi_period` | RSI smoothing period. |
| `oversold` | Oversold level used for long recovery entries. |
| `overbought` | Overbought level used for short recovery entries. |
| `exit_mid` | Midline used to close mean-reversion positions. |
| `allow_short` | Enables short-side signals. |

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
- `rsi`

## Example

```python
from shared.registry import StrategyRegistry

registry = StrategyRegistry()
strategy = registry.create(
    "rsi_reversion",
    {"rsi_period": 10, "oversold": 25.0, "overbought": 75.0, "exit_mid": 50.0},
)
result = strategy.run(df)
```

## Caveats

- In strong trends RSI can remain extreme for extended periods.
- Thresholds must satisfy `oversold < exit_mid < overbought`.
