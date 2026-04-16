"""Reporter for equity curve output."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


EQUITY_HEADERS = [
    "datetime",
    "cash",
    "equity",
    "close",
    "position_size",
    "position_price",
    "unrealized_pnl",
    "realized_pnl",
    "drawdown_pct",
]


def write_equity_report(
    equity_rows: list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """Persist equity curve points as CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=EQUITY_HEADERS)
        writer.writeheader()
        for row in equity_rows:
            writer.writerow({header: row.get(header) for header in EQUITY_HEADERS})

    return path
