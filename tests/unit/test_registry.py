from __future__ import annotations

import json

import pytest

from shared.registry import RegistryError, StrategyRegistry

MANIFEST = {
    "slug": "stub_strategy",
    "name": "Stub Strategy",
    "category": "trend",
    "version": "1.0.0",
    "description": "A registry test strategy",
    "direction": ["long", "short"],
    "class_name": "StubStrategy",
    "timeframes": ["1h"],
    "symbols": ["BTCUSDT"],
    "required_columns": ["open", "high", "low", "close", "volume"],
    "outputs": ["entry_long", "entry_short", "exit_long", "exit_short"],
    "parameters": {
        "length": {
            "type": "int",
            "default": 10,
            "min": 1,
            "max": 100,
            "step": 1,
            "optimize": True,
            "description": "Example window",
        }
    },
}

STRATEGY_CODE = """
from __future__ import annotations

from shared.base_strategy import BaseStrategy
from shared.types import StrategyValidationError


class StubStrategy(BaseStrategy):
    slug = "stub_strategy"
    name = "Stub Strategy"
    category = "trend"
    default_params = {"length": 10}

    def validate_params(self) -> None:
        if self.params["length"] < 1:
            raise StrategyValidationError("length must be positive")

    def compute_indicators(self, df):
        return df

    def generate_signals(self, df):
        df["entry_long"] = False
        df["entry_short"] = False
        df["exit_long"] = False
        df["exit_short"] = False
        return df
"""


def _write_strategy_package(root):
    strategy_dir = root / "strategies" / "trend" / "stub_strategy"
    strategy_dir.mkdir(parents=True)
    (strategy_dir / "manifest.json").write_text(json.dumps(MANIFEST), encoding="utf-8")
    (strategy_dir / "strategy.py").write_text(STRATEGY_CODE, encoding="utf-8")


def test_registry_discovers_manifests_and_creates_instances(tmp_path):
    _write_strategy_package(tmp_path)
    registry = StrategyRegistry(root=tmp_path)

    registry.discover()
    instance = registry.create("stub_strategy")

    assert registry.list_strategies()[0]["slug"] == "stub_strategy"
    assert instance.slug == "stub_strategy"


def test_registry_rejects_duplicate_slugs(tmp_path):
    _write_strategy_package(tmp_path)
    other_dir = tmp_path / "strategies" / "breakout" / "another_stub"
    other_dir.mkdir(parents=True)
    (other_dir / "manifest.json").write_text(json.dumps(MANIFEST), encoding="utf-8")
    (other_dir / "strategy.py").write_text(STRATEGY_CODE, encoding="utf-8")

    with pytest.raises(RegistryError, match="Duplicate strategy slug"):
        StrategyRegistry(root=tmp_path).discover()
