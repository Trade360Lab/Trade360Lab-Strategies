import backtrader as bt
from app.analyzers.analyzer_factory import add_default_analyzers


def build_cerebro(strategy_cls, data_feed, settings):
    cerebro = bt.Cerebro()

    cerebro.addstrategy(
        strategy_cls,
        enable_event_logging=settings.enable_event_logging,
        enable_bar_logging=settings.enable_bar_logging,
        log_level=settings.log_level,
        log_file=str(settings.log_file),
        logger_name=f"strategy.{settings.strategy_name}",
    )
    cerebro.adddata(data_feed)

    cerebro.broker.setcash(settings.cash)
    cerebro.broker.setcommission(commission=settings.commission)
    cerebro.addsizer(bt.sizers.FixedSize, stake=settings.stake)

    add_default_analyzers(cerebro)
    return cerebro
