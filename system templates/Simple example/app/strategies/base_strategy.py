"""Base strategy with reusable event logging hooks."""

from __future__ import annotations

import logging

import backtrader as bt

from app.logging.event_logger import EventLogger
from app.logging.logger import StructuredLogger, get_logger


class BaseStrategy(bt.Strategy):
    params = (
        ("risk_per_trade", 0.01),
        ("printlog", True),
        ("enable_event_logging", True),
        ("enable_bar_logging", False),
        ("log_level", "INFO"),
        ("log_file", "outputs/logs/strategy.log"),
        ("logger_name", "strategy"),
    )

    def __init__(self):
        self.order = None
        self.trade_count = 0
        self._peak_equity = float(self.broker.getvalue())
        self._last_signal_reason = None
        self._last_exit_reason = None
        self._logger = StructuredLogger(
            get_logger(
                self.p.logger_name,
                level=self.p.log_level,
                log_file=self.p.log_file,
            )
        )
        self.event_logger = EventLogger(
            self._logger,
            common_fields={"strategy": self.__class__.__name__},
        )
        self.build_indicators()

    def log(self, txt: str, *, level: str = "INFO") -> None:
        if not self.p.printlog:
            return
        self._logger.log(
            getattr(logging, level.upper(), logging.INFO),
            txt,
            event_type="strategy_log",
            datetime=self.datetime(),
        )

    def datetime(self):
        return self.datas[0].datetime.datetime(0)

    def current_drawdown_pct(self) -> float:
        equity = float(self.broker.getvalue())
        self._peak_equity = max(self._peak_equity, equity)
        if not self._peak_equity:
            return 0.0
        return (self._peak_equity - equity) / self._peak_equity * 100.0

    def signal_reason(self, signal_type: str) -> str | None:
        return f"{signal_type}_signal"

    def _log_bar(self) -> None:
        if not self.p.enable_event_logging or not self.p.enable_bar_logging:
            return
        self.event_logger.log_bar(
            datetime=self.datetime(),
            open=float(self.data.open[0]),
            high=float(self.data.high[0]),
            low=float(self.data.low[0]),
            close=float(self.data.close[0]),
            volume=float(self.data.volume[0]),
            cash=float(self.broker.getcash()),
            equity=float(self.broker.getvalue()),
            position_size=float(self.position.size),
            drawdown_pct=round(self.current_drawdown_pct(), 8),
        )

    def _log_signal(self, signal_type: str, reason: str | None) -> None:
        if not self.p.enable_event_logging:
            return
        self.event_logger.log_signal(
            datetime=self.datetime(),
            signal_type=signal_type,
            price=float(self.data.close[0]),
            reason=reason,
        )

    def _submit_order(self, side: str):
        if side == "buy":
            return self.buy()
        if side == "sell":
            return self.sell()
        return self.close()

    def build_indicators(self):
        """Переопределяется в дочерних классах"""
        pass

    def long_signal(self):
        return False

    def short_signal(self):
        return False

    def exit_signal(self):
        return False

    def notify_order(self, order):
        if self.p.enable_event_logging:
            self.event_logger.log_order(
                datetime=self.datetime(),
                status=order.getstatusname(),
                side="buy" if order.isbuy() else "sell",
                size=float(order.size or 0.0),
                created_price=float(order.created.price)
                if getattr(order, "created", None) is not None
                and order.created.price is not None
                else None,
                executed_price=float(order.executed.price)
                if getattr(order, "executed", None) is not None
                and order.executed.price is not None
                else None,
                commission=float(order.executed.comm)
                if getattr(order, "executed", None) is not None
                and order.executed.comm is not None
                else None,
            )

        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            side = "BUY" if order.isbuy() else "SELL"
            self.log(
                f"{side} EXECUTED | Price={order.executed.price:.2f}, "
                f"Size={order.executed.size}, Comm={order.executed.comm:.4f}"
            )
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"ORDER FAILED: {order.getstatusname()}")
            if self.p.enable_event_logging:
                self.event_logger.log_error(
                    datetime=self.datetime(),
                    status=order.getstatusname(),
                    side="buy" if order.isbuy() else "sell",
                )

        self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trade_count += 1
            self.log(
                f"TRADE CLOSED | Gross={trade.pnl:.2f}, Net={trade.pnlcomm:.2f}"
            )
            if self.p.enable_event_logging:
                self.event_logger.log_trade(
                    entry_dt=bt.num2date(getattr(trade, "dtopen", None))
                    if getattr(trade, "dtopen", None)
                    else None,
                    exit_dt=bt.num2date(getattr(trade, "dtclose", None))
                    if getattr(trade, "dtclose", None)
                    else self.datetime(),
                    side="long" if getattr(trade, "long", True) else "short",
                    entry_price=float(getattr(trade, "price", 0.0) or 0.0),
                    exit_price=float(self.data.close[0]),
                    size=float(getattr(trade, "size", 0.0) or 0.0),
                    pnl=float(getattr(trade, "pnl", 0.0) or 0.0),
                    pnl_net=float(getattr(trade, "pnlcomm", 0.0) or 0.0),
                    bars_held=int(getattr(trade, "barlen", 0) or 0),
                    exit_reason=self._last_exit_reason,
                )

    def next(self):
        self._log_bar()
        try:
            if self.order:
                return

            if not self.position:
                if self.long_signal():
                    self._last_signal_reason = self.signal_reason("long")
                    self._last_exit_reason = None
                    self.log("LONG SIGNAL")
                    self._log_signal("long", self._last_signal_reason)
                    self.order = self._submit_order("buy")
                elif self.short_signal():
                    self._last_signal_reason = self.signal_reason("short")
                    self._last_exit_reason = None
                    self.log("SHORT SIGNAL")
                    self._log_signal("short", self._last_signal_reason)
                    self.order = self._submit_order("sell")
            else:
                if self.exit_signal():
                    self._last_exit_reason = self.signal_reason("exit")
                    self.log("EXIT SIGNAL")
                    self._log_signal("exit", self._last_exit_reason)
                    self.order = self._submit_order("close")
        except Exception as exc:
            if self.p.enable_event_logging:
                self.event_logger.log_error(
                    datetime=self.datetime(),
                    error=str(exc),
                )
            raise
