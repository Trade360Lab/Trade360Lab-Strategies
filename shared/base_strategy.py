"""Base contract for all dataframe-based trading strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

import pandas as pd

from shared.types import Params, StrategyValidationError
from shared.validation import (
    validate_dataframe_not_empty,
    validate_no_duplicate_timestamps,
    validate_ohlcv_columns,
    validate_sorted_index_or_timestamp,
    validate_strategy_output,
)


class BaseStrategy(ABC):
    """Strict base class for strategy implementations.

    Strategies operate on OHLCV pandas data and must emit the standard signal
    columns without using future information.
    """

    slug: ClassVar[str]
    name: ClassVar[str]
    category: ClassVar[str]
    default_params: ClassVar[dict[str, Any]] = {}

    def __init__(self, params: Params | None = None) -> None:
        merged_params = dict(self.default_params)
        if params:
            merged_params.update(params)
        self.params: Params = merged_params
        self.validate_params()

    @abstractmethod
    def validate_params(self) -> None:
        """Validate the strategy parameters stored in ``self.params``."""

    @abstractmethod
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all derived indicator columns required by the strategy."""

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Populate the standard signal columns on the provided dataframe."""

    def validate_input_data(self, df: pd.DataFrame) -> None:
        """Perform minimal contract validation before processing."""

        if not isinstance(df, pd.DataFrame):
            raise StrategyValidationError("Strategy input must be a pandas DataFrame.")
        validate_dataframe_not_empty(df)
        validate_ohlcv_columns(df)
        validate_sorted_index_or_timestamp(df)
        validate_no_duplicate_timestamps(df)

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run the full strategy pipeline on a defensive copy of ``df``."""

        self.validate_input_data(df)
        result = df.copy(deep=True)
        result = self.compute_indicators(result)
        result = self.generate_signals(result)

        validate_strategy_output(result)
        return result
