"""Custom analyzer for aggregate performance metrics."""

from __future__ import annotations

from dataclasses import dataclass

import backtrader as bt


@dataclass(slots=True)
class _TradeStats:
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_bars_in_trade: int = 0
    total_commission: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    _current_wins: int = 0
    _current_losses: int = 0

    def register_trade(
        self, pnl: float, pnl_net: float, bars_held: int, commission: float
    ) -> None:
        self.total_trades += 1
        self.total_bars_in_trade += bars_held
        self.total_commission += commission
        self.net_pnl += pnl_net

        if pnl_net > 0:
            self.gross_profit += pnl_net
            self.winning_trades += 1
            self._current_wins += 1
            self._current_losses = 0
            self.max_consecutive_wins = max(self.max_consecutive_wins, self._current_wins)
            return

        if pnl_net < 0:
            self.gross_loss += abs(pnl_net)
            self.losing_trades += 1
            self._current_losses += 1
            self._current_wins = 0
            self.max_consecutive_losses = max(
                self.max_consecutive_losses, self._current_losses
            )
            return

        if pnl > 0:
            self.winning_trades += 1
        elif pnl < 0:
            self.losing_trades += 1
        self._current_wins = 0
        self._current_losses = 0


class PerformanceAnalyzer(bt.Analyzer):
    """Collect robust portfolio and trade-level performance metrics."""

    def start(self) -> None:
        self.start_cash = float(getattr(self.strategy.broker, "startingcash", 0.0))
        self.end_value = self.start_cash
        self._bar_count = 0
        self._bars_with_exposure = 0
        self._stats = _TradeStats()

    def next(self) -> None:
        self._bar_count += 1
        if self.strategy.position.size:
            self._bars_with_exposure += 1

    def notify_trade(self, trade: bt.Trade) -> None:
        if not trade.isclosed:
            return

        pnl = float(getattr(trade, "pnl", 0.0) or 0.0)
        pnl_net = float(getattr(trade, "pnlcomm", pnl) or pnl)
        bars_held = int(getattr(trade, "barlen", 0) or 0)
        commission = float(pnl - pnl_net)
        self._stats.register_trade(pnl, pnl_net, bars_held, commission)

    def stop(self) -> None:
        self.end_value = float(self.strategy.broker.getvalue())

    def get_analysis(self) -> dict[str, float | int]:
        total_trades = self._stats.total_trades
        net_profit = self.end_value - self.start_cash
        net_profit_pct = (net_profit / self.start_cash * 100.0) if self.start_cash else 0.0
        win_rate = (self._stats.winning_trades / total_trades * 100.0) if total_trades else 0.0
        loss_rate = (self._stats.losing_trades / total_trades * 100.0) if total_trades else 0.0
        average_win = (
            self._stats.gross_profit / self._stats.winning_trades
            if self._stats.winning_trades
            else 0.0
        )
        average_loss = (
            self._stats.gross_loss / self._stats.losing_trades
            if self._stats.losing_trades
            else 0.0
        )
        payoff_ratio = (average_win / average_loss) if average_loss else 0.0
        profit_factor = (
            self._stats.gross_profit / self._stats.gross_loss
            if self._stats.gross_loss
            else 0.0
        )
        expectancy = (self._stats.net_pnl / total_trades) if total_trades else 0.0
        avg_bars_in_trade = (
            self._stats.total_bars_in_trade / total_trades if total_trades else 0.0
        )
        exposure_pct = (
            self._bars_with_exposure / self._bar_count * 100.0 if self._bar_count else 0.0
        )

        return {
            "start_cash": round(self.start_cash, 8),
            "end_value": round(self.end_value, 8),
            "net_profit": round(net_profit, 8),
            "net_profit_pct": round(net_profit_pct, 8),
            "gross_profit": round(self._stats.gross_profit, 8),
            "gross_loss": round(self._stats.gross_loss, 8),
            "win_rate": round(win_rate, 8),
            "loss_rate": round(loss_rate, 8),
            "total_trades": total_trades,
            "winning_trades": self._stats.winning_trades,
            "losing_trades": self._stats.losing_trades,
            "average_win": round(average_win, 8),
            "average_loss": round(average_loss, 8),
            "payoff_ratio": round(payoff_ratio, 8),
            "profit_factor": round(profit_factor, 8),
            "expectancy": round(expectancy, 8),
            "max_consecutive_wins": self._stats.max_consecutive_wins,
            "max_consecutive_losses": self._stats.max_consecutive_losses,
            "avg_bars_in_trade": round(avg_bars_in_trade, 8),
            "exposure_pct": round(exposure_pct, 8),
            "total_commission": round(self._stats.total_commission, 8),
        }
