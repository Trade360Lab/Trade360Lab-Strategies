"""PullbackTrader runtime entrypoint."""

from __future__ import annotations

import time
from logging import Logger

from .config import AppConfig
from .execution import (
    BaseExecutionClient,
    LiveExecutionClient,
    PaperExecutionClient,
    calculate_position_size,
)
from .market import BaseMarketDataClient, PollingBinanceMarketDataClient
from .models import BotState, Candle, Signal
from .storage import append_signal, append_trade, load_state, save_state
from .strategy import TrendPullbackStrategy
from .utils import round_price, setup_logger, utc_now


class PullbackTraderRuntime:
    """Compose and run the production-like runtime loop."""

    def __init__(self, config: AppConfig, logger: Logger) -> None:
        self.config = config
        self.logger = logger
        self.market: BaseMarketDataClient = PollingBinanceMarketDataClient(config.market, logger)
        self.strategy = TrendPullbackStrategy(
            config=config.strategy,
            symbol=config.market.symbol,
            timeframe=config.market.timeframe,
            logger=logger,
        )
        self.execution: BaseExecutionClient = self._build_execution_client()
        self.state: BotState = load_state(config.storage, config)
        self.buffer: list[Candle] = []

    def _build_execution_client(self) -> BaseExecutionClient:
        if self.config.execution.paper_mode:
            return PaperExecutionClient(self.config.execution, self.logger)
        return LiveExecutionClient(self.config.execution, self.logger)

    def bootstrap(self) -> None:
        """Load history, reconcile local state and recover missed candles after restart."""

        self.execution.sync_state(self.state)
        self.buffer = self.market.load_initial_history(self.config.market.history_limit)
        if not self.buffer:
            raise RuntimeError("Initial history is empty. Bot cannot start.")

        self.logger.info(
            "Loaded %s candles for %s %s",
            len(self.buffer),
            self.config.market.symbol,
            self.config.market.timeframe,
        )

        if self.state.last_processed_candle_time is None:
            self.state.last_processed_candle_time = self.buffer[-1].close_time
            self.state.last_sync_time = utc_now()
            save_state(self.config.storage, self.state)
            self.logger.info(
                "Fresh start detected. Warmed up buffer through %s and waiting for the next close.",
                self.buffer[-1].close_time.isoformat(),
            )
            return

        missed = [candle for candle in self.buffer if candle.close_time > self.state.last_processed_candle_time]
        if missed:
            self.logger.warning("Recovering %s missed closed candle(s) from local history.", len(missed))
            self.state.recovery_required = False
            for candle in missed:
                self._process_candle(candle)
        elif self.state.position is not None and self.buffer[0].close_time > self.state.position.entry_time:
            self.state.recovery_required = True
            self.logger.warning(
                "Candle buffer does not reach the recorded entry time. Timeout recovery may need exchange sync."
            )
            save_state(self.config.storage, self.state)

    def run(self) -> None:
        """Run the main closed-candle loop."""

        self.bootstrap()

        while True:
            try:
                next_candle = self.market.wait_for_next_closed_candle(self.state.last_processed_candle_time)
                self._process_candle(next_candle)
            except KeyboardInterrupt:
                self.logger.info("Shutdown requested by operator.")
                raise
            except Exception as exc:
                self.state.last_error = str(exc)
                save_state(self.config.storage, self.state)
                self.logger.exception("Runtime loop error: %s", exc)
                time.sleep(self.config.loop_error_sleep_seconds)

    def _process_candle(self, candle: Candle) -> None:
        """Process one closed candle end-to-end."""

        self.buffer = self.market.update_candle_buffer(
            self.buffer,
            candle,
            self.config.market.history_limit,
        )
        self.state.last_processed_candle_time = candle.close_time
        self.state.last_sync_time = utc_now()

        if self.state.kill_switch or self.config.kill_switch:
            self.logger.warning("Kill switch active. Skipping trading logic for candle %s.", candle.close_time.isoformat())
            save_state(self.config.storage, self.state)
            return

        self.execution.sync_state(self.state)
        position = self.execution.get_position()
        signal = self.strategy.evaluate(self.buffer, position)

        if position is not None:
            position.bars_held = max(position.bars_held, sum(1 for item in self.buffer if item.close_time > position.entry_time))
            position.last_update_time = utc_now()

        if signal.action == "entry":
            self._prepare_entry(signal)

        append_signal(self.config.storage, signal)

        if signal.action == "entry" and (signal.quantity or 0.0) > 0:
            result = self.execution.place_entry(signal)
            self._handle_order_result(result)
        elif signal.action == "exit":
            result = self.execution.close_position(signal.reason, signal)
            self._handle_order_result(result)

        save_state(self.config.storage, self.state)

    def _prepare_entry(self, signal: Signal) -> None:
        """Apply notebook-equivalent risk sizing before sending an entry order."""

        if signal.entry_price is None or signal.stop_price is None:
            signal.quantity = 0.0
            signal.reason = "entry_missing_prices"
            return

        quantity = calculate_position_size(
            cash=self.state.available_cash,
            entry_price=signal.entry_price,
            stop_price=signal.stop_price,
            risk_per_trade=self.config.strategy.risk_per_trade,
            quantity_step=self.config.execution.quantity_step,
            min_quantity=self.config.execution.min_quantity,
        )
        signal.quantity = quantity
        signal.entry_price = round_price(signal.entry_price, self.config.execution.price_step)
        signal.stop_price = round_price(signal.stop_price, self.config.execution.price_step)
        signal.take_price = round_price(signal.take_price or 0.0, self.config.execution.price_step)
        if quantity <= 0:
            self.logger.warning("Entry signal rejected because calculated quantity is zero.")

    def _handle_order_result(self, result) -> None:
        """Persist order result and update local state."""

        if not result.accepted:
            self.state.last_error = result.reason
            self.logger.warning("Order rejected: %s", result.reason)
            return

        append_trade(self.config.storage, result)
        self.state.available_cash = getattr(self.execution, "cash", self.state.available_cash)
        self.state.position = result.position
        self.state.last_order_time = result.timestamp
        self.state.last_signal_time = result.timestamp
        self.state.last_error = None
        self.logger.info(
            "Order %s filled | symbol=%s | qty=%.8f | price=%s | reason=%s",
            result.action,
            result.symbol,
            result.quantity,
            result.filled_price,
            result.reason,
        )


def main() -> None:
    """Program entrypoint."""

    config = AppConfig.from_env()
    logger = setup_logger(config.app_name, config.log_level, config.storage.logs_path)
    runtime = PullbackTraderRuntime(config, logger)
    runtime.run()


if __name__ == "__main__":
    main()
