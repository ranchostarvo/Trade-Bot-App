from decimal import Decimal

from app.api.control_plane import ControlPlane
from app.storage import SQLiteStore
from app.trading.runtime import TradingRuntime


class ReadOnlyBroker:
    def order_status(self, order_id):
        raise AssertionError("No broker order lookup expected.")


def test_control_plane_uses_runtime_fleet_and_durable_audit(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    runtime = TradingRuntime.build(
        account_cash=Decimal("50000"),
        account_equity=Decimal("100000"),
        reconciler=ReadOnlyBroker(),
        store=store,
    )
    control = ControlPlane.build(runtime)

    assert control.fleet is runtime.fleet
    assert control.audit.store is store
    assert control.trading_ready is True


def test_control_plane_fails_closed_without_restart_recovery():
    runtime = TradingRuntime.build(account_cash=Decimal("50000"))
    control = ControlPlane.build(runtime)

    assert control.trading_ready is False
    assert runtime.kill_switch.engaged is True
