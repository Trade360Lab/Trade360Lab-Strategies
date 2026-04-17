# Donchian Breakout

`donchian_breakout` is a breakout strategy based on prior Donchian channel boundaries.

## Logic

- `entry_long`: close crosses above the prior upper Donchian band.
- `exit_long`: close crosses below the prior exit-channel midline.
- `entry_short`: optional mirror logic when close crosses below the prior lower band.
- `exit_short`: optional mirror logic when close crosses back above the prior exit midline.

The strategy uses shifted channel values for all trigger conditions, so the current bar is never compared against a channel that already includes its own high or low.

## Parameters

| Name | Description |
| --- | --- |
| `lookback` | Donchian lookback used for entries. |
| `exit_lookback` | Donchian lookback used for exit midline. |
| `allow_short` | Enables short-side breakout signals. |

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
- `donchian_upper`
- `donchian_lower`
- `donchian_mid`
- `donchian_exit_upper`
- `donchian_exit_lower`
- `donchian_exit_mid`

## Example

```python
from shared.registry import StrategyRegistry

registry = StrategyRegistry()
strategy = registry.create(
    "donchian_breakout",
    {"lookback": 55, "exit_lookback": 20, "allow_short": True},
)
result = strategy.run(df)
```

## Caveats

- Breakout systems can whipsaw during range-bound markets.
- Signals are sparser on higher lookback windows.
