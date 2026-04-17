"""Helpers for extracting structured analyzer results."""

from __future__ import annotations

from typing import Any

import backtrader as bt

from app.config import Settings


def _analyzer_payload(strategy: Any, name: str, default: Any) -> Any:
    analyzer = getattr(strategy.analyzers, name, None)
    if analyzer is None:
        return default
    return analyzer.get_analysis()


def _extract_metadata(strategy: Any, settings: Settings | None = None) -> dict[str, Any]:
    data = strategy.datas[0]
    if len(data):
        start_dt = bt.num2date(data.datetime.array[0]).isoformat()
        end_dt = bt.num2date(data.datetime.array[-1]).isoformat()
    else:
        start_dt = None
        end_dt = None
    data_name = getattr(strategy.datas[0], "_name", "") or getattr(strategy.datas[0], "_dataname", "")
    symbol = settings.symbol if settings is not None else str(data_name).split("_")[0].upper()
    timeframe = settings.timeframe if settings is not None else None
    return {
        "strategy_name": strategy.__class__.__name__,
        "symbol": symbol,
        "timeframe": timeframe,
        "start_datetime": start_dt,
        "end_datetime": end_dt,
    }


def _build_summary(
    metadata: dict[str, Any],
    performance: dict[str, Any],
    drawdown: dict[str, Any],
    sharpe: dict[str, Any],
) -> dict[str, Any]:
    max_drawdown_pct = float(drawdown.get("max", {}).get("drawdown", 0.0) or 0.0)
    sharpe_value = sharpe.get("sharperatio")
    return {
        **metadata,
        "start_cash": performance.get("start_cash", 0.0),
        "end_value": performance.get("end_value", 0.0),
        "return_pct": performance.get("net_profit_pct", 0.0),
        "total_trades": performance.get("total_trades", 0),
        "win_rate": performance.get("win_rate", 0.0),
        "profit_factor": performance.get("profit_factor", 0.0),
        "expectancy": performance.get("expectancy", 0.0),
        "sharpe": sharpe_value if sharpe_value is not None else 0.0,
        "max_drawdown_pct": max_drawdown_pct,
    }


def extract_results(strategy: Any, settings: Settings | None = None) -> dict[str, Any]:
    """Return standard and custom analyzer results in a stable structure."""
    sharpe = _analyzer_payload(strategy, "sharpe", {})
    drawdown = _analyzer_payload(strategy, "drawdown", {})
    trades = _analyzer_payload(strategy, "trades", {})
    returns = _analyzer_payload(strategy, "returns", {})
    performance = _analyzer_payload(strategy, "performance", {})
    trade_journal = _analyzer_payload(strategy, "trade_journal", {"trades": []})
    equity_curve = _analyzer_payload(strategy, "equity", [])
    metadata = _extract_metadata(strategy, settings=settings)

    return {
        "metadata": metadata,
        "summary": _build_summary(metadata, performance, drawdown, sharpe),
        "standard": {
            "sharpe": sharpe,
            "drawdown": drawdown,
            "trades": trades,
            "returns": returns,
        },
        "custom": {
            "performance": performance,
            "trade_journal": trade_journal,
            "equity_curve": equity_curve,
        },
    }
