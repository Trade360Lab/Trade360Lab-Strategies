from app.strategies.sma_cross import SmaCrossStrategy
from app.strategies.breakout import BreakoutStrategy

STRATEGY_REGISTRY = {
    "sma_cross": SmaCrossStrategy,
    "breakout": BreakoutStrategy,
}