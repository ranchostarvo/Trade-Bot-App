from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.runtime import TradingRuntime


class ReadOnlyBroker:
    def order_status(self, order_id):
        return "filled"


def test_runtime_wires_one_shared_kill_switch_with_durable_services(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    runtime = TradingRuntime.build(
        account_cash=Decimal("50000"),
        account_equity=Decimal("100000"),
        reconciler=ReadOnlyBroker(),
        store=store,
    )

    assert runtime.fleet.kill_switch is runtime.kill_switch
    assert runtime.risk.kill_switch is runtime.kill_switch
    assert runtime.execution.risk_engine is runtime.risk
    assert runtime.resources.store is store
    assert runtime.settlement.resources is runtime.resources
    assert runtime.broker_orders.store is store
    assert runtime.restart_recovery.store is store
    assert runtime.restart_recovery.kill_switch is runtime.kill_switch


def test_runtime_requires_equity_for_durable_resources(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    try:
        TradingRuntime.build(Decimal("50000"), store=store)
    except ValueError as exc:
        assert "account_equity" in str(exc)
    else:
        raise AssertionError("Expected durable runtime without equity to fail.")
