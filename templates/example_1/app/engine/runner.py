"""Backtest execution entrypoints."""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.engine.results import extract_results
from app.logging.event_logger import EventLogger
from app.logging.logger import StructuredLogger, get_logger
from app.reporters.equity_reporter import write_equity_report
from app.reporters.summary_reporter import write_summary_report
from app.reporters.trades_reporter import write_trades_report


def _write_reports(report: dict[str, Any], settings: Settings) -> dict[str, str]:
    return {
        "summary": str(write_summary_report(report["summary"], settings.summary_report_path)),
        "trades": str(
            write_trades_report(
                report["custom"]["trade_journal"], settings.trades_report_path
            )
        ),
        "equity_curve": str(
            write_equity_report(
                report["custom"]["equity_curve"], settings.equity_report_path
            )
        ),
    }


def run_backtest(cerebro, plot: bool = False, settings: Settings | None = None):
    """Run the backtest and persist generated artifacts when settings are provided."""
    results = cerebro.run()
    strategy = results[0]
    report = extract_results(strategy, settings=settings)

    if settings is not None:
        artifact_paths = _write_reports(report, settings)
        report["artifacts"] = artifact_paths
        run_logger = EventLogger(
            StructuredLogger(
                get_logger(
                    "backtest.runner",
                    level=settings.log_level,
                    log_file=settings.log_file,
                )
            )
        )
        run_logger.log_run_summary(
            strategy_name=report["summary"]["strategy_name"],
            symbol=report["summary"]["symbol"],
            timeframe=report["summary"]["timeframe"],
            start_cash=report["summary"]["start_cash"],
            final_value=report["summary"]["end_value"],
            return_pct=report["summary"]["return_pct"],
            max_drawdown_pct=report["summary"]["max_drawdown_pct"],
            sharpe=report["summary"]["sharpe"],
            trades_total=report["summary"]["total_trades"],
        )

    if plot:
        cerebro.plot()

    return report
