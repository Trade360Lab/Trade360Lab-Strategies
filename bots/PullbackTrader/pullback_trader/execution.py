"""Execution clients and risk sizing for PullbackTrader."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from logging import Logger

from .config import ExecutionConfig
from .models import BotState, OrderResult, PositionState, Signal
from .utils import round_price, round_quantity, utc_now


def calculate_position_size(
    cash: float,
    entry_price: float,
    stop_price: float,
    risk_per_trade: float,
    quantity_step: float,
    min_quantity: float,
) -> float:
    """Notebook-equivalent position sizing based on cash risk and stop distance."""

    stop_distance = entry_price - stop_price
    if stop_distance <= 0 or entry_price <= 0 or cash <= 0:
        return 0.0

    risk_amount = cash * risk_per_trade
    raw_size = risk_amount / stop_distance
    max_affordable = cash / entry_price
    size = min(raw_size, max_affordable)
    return round_quantity(size, quantity_step, min_quantity)


class BaseExecutionClient(ABC):
    """Abstract execution client. Live exchange adapters should implement this API."""

    def __init__(self, config: ExecutionConfig, logger: Logger) -> None:
        self.config = config
        self.logger = logger

    @abstractmethod
    def get_position(self) -> PositionState | None:
        """Return the current exchange-side position."""

    @abstractmethod
    def place_entry(self, signal: Signal) -> OrderResult:
        """Place a long entry order from a strategy signal."""

    @abstractmethod
    def close_position(self, reason: str, signal: Signal | None = None) -> OrderResult:
        """Close the current position."""

    @abstractmethod
    def sync_state(self, bot_state: BotState | None = None) -> BotState | None:
        """Reconcile execution-side state with local state."""


class PaperExecutionClient(BaseExecutionClient):
    """Simple paper execution client for closed-candle runtime testing."""

    def __init__(self, config: ExecutionConfig, logger: Logger) -> None:
        super().__init__(config, logger)
        self.cash = config.initial_cash
        self.position: PositionState | None = None

    def get_position(self) -> PositionState | None:
        return self.position

    def place_entry(self, signal: Signal) -> OrderResult:
        if signal.action != "entry" or signal.entry_price is None or signal.quantity is None:
            return self._rejected_result("entry", signal, "invalid_entry_signal")

        if self.position is not None:
            return self._rejected_result("entry", signal, "position_already_open")

        fill_price = round_price(signal.entry_price * (1 + self.config.slippage_pct), self.config.price_step)
        quantity = signal.quantity
        gross_cost = fill_price * quantity
        entry_fee = gross_cost * self.config.fee_rate
        total_cost = gross_cost + entry_fee

        if total_cost > self.cash:
            return self._rejected_result("entry", signal, "insufficient_cash")

        self.cash -= total_cost
        self.position = PositionState(
            symbol=signal.symbol,
            side=signal.side,
            quantity=quantity,
            entry_price=fill_price,
            entry_time=signal.timestamp,
            stop_price=signal.stop_price or 0.0,
            take_price=signal.take_price or 0.0,
            strategy_name=signal.strategy_name,
            entry_reason=signal.reason,
            bars_held=0,
            last_update_time=utc_now(),
        )

        return OrderResult(
            accepted=True,
            status="filled",
            action="entry",
            symbol=signal.symbol,
            side=signal.side,
            quantity=quantity,
            requested_price=signal.entry_price,
            filled_price=fill_price,
            reason=signal.reason,
            timestamp=utc_now(),
            order_id=f"paper-entry-{int(datetime.now().timestamp())}",
            position=self.position,
            raw={"mode": "paper", "fee": entry_fee},
        )

    def close_position(self, reason: str, signal: Signal | None = None) -> OrderResult:
        if self.position is None:
            now = utc_now()
            return OrderResult(
                accepted=False,
                status="rejected",
                action="exit",
                symbol="",
                side="long",
                quantity=0.0,
                requested_price=None,
                filled_price=None,
                reason="no_open_position",
                timestamp=now,
            )

        requested_price = signal.exit_price if signal is not None else self.position.entry_price
        if requested_price is None:
            requested_price = self.position.entry_price

        fill_price = round_price(requested_price * (1 - self.config.slippage_pct), self.config.price_step)
        quantity = self.position.quantity
        proceeds = fill_price * quantity
        exit_fee = proceeds * self.config.fee_rate
        entry_fee = self.position.entry_price * quantity * self.config.fee_rate
        realized_pnl = (fill_price - self.position.entry_price) * quantity - entry_fee - exit_fee

        self.cash += proceeds - exit_fee
        closed_position = self.position
        self.position = None

        return OrderResult(
            accepted=True,
            status="filled",
            action="exit",
            symbol=closed_position.symbol,
            side=closed_position.side,
            quantity=quantity,
            requested_price=requested_price,
            filled_price=fill_price,
            reason=reason,
            timestamp=utc_now(),
            order_id=f"paper-exit-{int(datetime.now().timestamp())}",
            realized_pnl=realized_pnl,
            position=None,
            raw={"mode": "paper", "fee": exit_fee},
        )

    def sync_state(self, bot_state: BotState | None = None) -> BotState | None:
        if bot_state is None:
            return None

        self.cash = bot_state.available_cash
        self.position = bot_state.position
        bot_state.last_sync_time = utc_now()
        return bot_state

    def _rejected_result(self, action: str, signal: Signal, reason: str) -> OrderResult:
        return OrderResult(
            accepted=False,
            status="rejected",
            action=action,
            symbol=signal.symbol,
            side=signal.side,
            quantity=signal.quantity or 0.0,
            requested_price=signal.entry_price,
            filled_price=None,
            reason=reason,
            timestamp=utc_now(),
        )


class LiveExecutionClient(BaseExecutionClient):
    """Placeholder for a future live exchange adapter."""

    def __init__(self, config: ExecutionConfig, logger: Logger) -> None:
        super().__init__(config, logger)
        self.position: PositionState | None = None

    def get_position(self) -> PositionState | None:
        return self.position

    def place_entry(self, signal: Signal) -> OrderResult:
        raise NotImplementedError("LiveExecutionClient.place_entry must be implemented for a real exchange.")

    def close_position(self, reason: str, signal: Signal | None = None) -> OrderResult:
        raise NotImplementedError("LiveExecutionClient.close_position must be implemented for a real exchange.")

    def sync_state(self, bot_state: BotState | None = None) -> BotState | None:
        self.logger.warning("LiveExecutionClient.sync_state is a skeleton and does not query the exchange yet.")
        if bot_state is not None:
            bot_state.last_sync_time = utc_now()
        return bot_state
