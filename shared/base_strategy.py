"""Base contract for all dataframe-based trading strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

import pandas as pd

from shared.types import Params, REQUIRED_OHLCV_COLUMNS, REQUIRED_SIGNAL_COLUMNS


class StrategyValidationError(ValueError):
    """Raised when strategy inputs or parameters violate the contract."""


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
        if df.empty:
            raise StrategyValidationError("Strategy input DataFrame must not be empty.")
        missing = [column for column in REQUIRED_OHLCV_COLUMNS if column not in df.columns]
        if missing:
            raise StrategyValidationError(
                "Strategy input is missing required OHLCV columns: "
                + ", ".join(missing)
            )

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run the full strategy pipeline on a defensive copy of ``df``."""

        self.validate_input_data(df)
        result = df.copy(deep=True)
        result = self.compute_indicators(result)
        result = self.generate_signals(result)

        missing_outputs = [
            column for column in REQUIRED_SIGNAL_COLUMNS if column not in result.columns
        ]
        if missing_outputs:
            raise StrategyValidationError(
                "Strategy output is missing required signal columns: "
                + ", ".join(missing_outputs)
            )

        for column in REQUIRED_SIGNAL_COLUMNS:
            result[column] = result[column].astype(bool)

        return result
