from __future__ import annotations

from pprint import pprint
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import Settings
from app.data.loaders import load_csv_to_bt
from app.engine.cerebro_builder import build_cerebro
from app.engine.runner import run_backtest
from app.utils.registry import STRATEGY_REGISTRY


def main():
    settings = Settings()

    strategy_cls = STRATEGY_REGISTRY[settings.strategy_name]
    data_feed = load_csv_to_bt(settings.data_path)

    cerebro = build_cerebro(strategy_cls, data_feed, settings)
    report = run_backtest(cerebro, plot=settings.plot, settings=settings)

    pprint(report)


if __name__ == "__main__":
    main()
