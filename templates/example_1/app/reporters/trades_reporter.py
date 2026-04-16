"""Reporter for the backtest trade journal."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


TRADE_HEADERS = [
    "trade_id",
    "direction",
    "entry_dt",
    "exit_dt",
    "entry_price",
    "exit_price",
    "size",
    "pnl",
    "pnl_net",
    "commission",
    "bars_held",
    "mae",
    "mfe",
    "exit_reason",
    "signal_reason",
]


def write_trades_report(
    trades_payload: dict[str, list[dict[str, Any]]] | list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """Persist trades as CSV, creating headers even when there are no rows."""
    rows = (
        trades_payload.get("trades", [])
        if isinstance(trades_payload, dict)
        else trades_payload
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=TRADE_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header) for header in TRADE_HEADERS})

    return path
