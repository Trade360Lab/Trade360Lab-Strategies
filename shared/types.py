"""Shared type aliases and dataclasses used across the strategy library."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, TypedDict

import pandas as pd

Category = Literal["trend", "mean_reversion", "breakout", "experimental"]
Direction = Literal["long", "short"]
DataFrame = pd.DataFrame
Series = pd.Series
Params = dict[str, Any]

REQUIRED_OHLCV_COLUMNS: tuple[str, ...] = ("open", "high", "low", "close", "volume")
REQUIRED_SIGNAL_COLUMNS: tuple[str, ...] = (
    "entry_long",
    "entry_short",
    "exit_long",
    "exit_short",
)
OPTIONAL_SIGNAL_COLUMNS: tuple[str, ...] = (
    "stop_loss",
    "take_profit",
    "signal_score",
    "regime",
)


class ParameterDefinition(TypedDict, total=False):
    """Normalized strategy parameter description loaded from a manifest."""

    type: str
    default: Any
    min: float | int
    max: float | int
    step: float | int
    options: list[Any]
    optimize: bool
    description: str


@dataclass(frozen=True, slots=True)
class StrategyMetadata:
    """Basic strategy metadata mirrored by the manifest."""

    slug: str
    name: str
    category: str
    version: str
    description: str
    direction: tuple[str, ...]
    class_name: str


@dataclass(frozen=True, slots=True)
class StrategyContext:
    """Container passed around when a registry creates a strategy instance."""

    metadata: StrategyMetadata
    manifest: Mapping[str, Any]

