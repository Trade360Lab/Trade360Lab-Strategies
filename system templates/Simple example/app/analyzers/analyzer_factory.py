import backtrader as bt
from app.analyzers.equity_analyzer import EquityAnalyzer
from app.analyzers.performance_analyzer import PerformanceAnalyzer
from app.analyzers.trade_journal_analyzer import TradeJournalAnalyzer


def add_default_analyzers(cerebro: bt.Cerebro) -> None:
    """Attach standard and project-specific analyzers to Cerebro."""
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(PerformanceAnalyzer, _name="performance")
    cerebro.addanalyzer(TradeJournalAnalyzer, _name="trade_journal")
    cerebro.addanalyzer(EquityAnalyzer, _name="equity")
