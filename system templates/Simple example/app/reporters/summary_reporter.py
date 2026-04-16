"""Reporter for the aggregate backtest summary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def write_summary_report(summary: dict[str, Any], output_path: str | Path) -> Path:
    """Persist summary metrics as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(summary, ensure_ascii=True, indent=2, default=_json_default) + "\n",
        encoding="utf-8",
    )
    return path
