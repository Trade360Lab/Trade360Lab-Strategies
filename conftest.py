"""Pytest fixtures shared across the entire repository."""

from __future__ import annotations

import pytest

from tests.fixtures.ohlcv_fixture import make_ohlcv_fixture


@pytest.fixture()
def ohlcv_df():
    """Return a deterministic OHLCV dataframe for strategy tests."""

    return make_ohlcv_fixture()
