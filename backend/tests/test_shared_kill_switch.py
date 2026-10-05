from decimal import Decimal

from app.trading.risk import AccountRiskState, OrderRequest, RiskRejected
from app.trading.runtime import TradingRuntime


def buy():
    return OrderRequest(
        symbol="SPY",
        side="buy",
        quantity=Decimal("1"),
        estimated_price=Decimal("100"),
    )


def test_runtime_shares_one_global_kill_switch():
    runtime = TradingRuntime.build(Decimal("50000"))
    assert runtime.fleet.kill_switch is runtime.kill_switch
    assert runtime.risk.kill_switch is runtime.kill_switch


def test_daily_loss_trip_blocks_entire_fleet():
    runtime = TradingRuntime.build(Decimal("50000"))
    runtime.fleet.provision(
        __import__(
            "app.trading.orchestrator",
            fromlist=["BotSpec"],
        ).BotSpec("bot-1", Decimal("500"))
    )
    runtime.fleet.start("bot-1")

    try:
        runtime.execution.execute(
            buy(),
            account_state=AccountRiskState(
                start_of_day_equity=Decimal("100000"),
                current_equity=Decimal("97500"),
            ),
        )
    except RiskRejected:
        pass
    else:
        raise AssertionError("Daily loss limit did not reject order.")

    assert runtime.kill_switch.engaged is True

    try:
        runtime.fleet.provision(
            __import__(
                "app.trading.orchestrator",
                fromlist=["BotSpec"],
            ).BotSpec("bot-2", Decimal("500"))
        )
    except RuntimeError:
        return
    raise AssertionError("Fleet accepted work after global kill switch trip.")
