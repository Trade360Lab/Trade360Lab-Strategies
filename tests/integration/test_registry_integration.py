from __future__ import annotations

from shared.registry import StrategyRegistry
from strategies.breakout.donchian_breakout.strategy import DonchianBreakoutStrategy
from strategies.mean_reversion.rsi_reversion.strategy import RSIReversionStrategy
from strategies.trend.ema_cross.strategy import EMACrossStrategy


def test_registry_discovers_all_repository_strategies():
    registry = StrategyRegistry()

    strategies = registry.list_strategies()
    slugs = {item["slug"] for item in strategies}

    assert {"ema_cross", "rsi_reversion", "donchian_breakout"}.issubset(slugs)


def test_registry_imports_all_repository_strategies():
    registry = StrategyRegistry()

    registry.discover()
    registry.smoke_test_imports()

    assert registry.get_strategy_class("ema_cross") is EMACrossStrategy
    assert registry.get_strategy_class("rsi_reversion") is RSIReversionStrategy
    assert registry.get_strategy_class("donchian_breakout") is DonchianBreakoutStrategy


def test_registry_create_returns_correct_instance_types():
    registry = StrategyRegistry()

    assert isinstance(registry.create("ema_cross"), EMACrossStrategy)
    assert isinstance(registry.create("rsi_reversion"), RSIReversionStrategy)
    assert isinstance(registry.create("donchian_breakout"), DonchianBreakoutStrategy)
