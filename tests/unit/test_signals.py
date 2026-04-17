from __future__ import annotations

import pandas as pd

from shared.signals import bars_since, crossover, crossunder, debounce_signal


def test_crossover_and_crossunder_detect_expected_events():
    left = pd.Series([1, 2, 3, 2, 1], dtype=float)
    right = pd.Series([2, 2, 2, 2, 2], dtype=float)

    assert crossover(left, right).tolist() == [False, False, True, False, False]
    assert crossunder(left, right).tolist() == [False, False, False, False, True]


def test_bars_since_counts_from_latest_true():
    condition = pd.Series([False, True, False, False, True, False])
    result = bars_since(condition).tolist()

    assert pd.isna(result[0])
    assert result[1:] == [0.0, 1.0, 2.0, 0.0, 1.0]


def test_debounce_signal_applies_cooloff():
    condition = pd.Series([True, True, False, True, False, True])

    assert debounce_signal(condition, cooloff_bars=1).tolist() == [
        True,
        False,
        False,
        True,
        False,
        True,
    ]
