from app.storage import SQLiteStore
from app.trading.order_state import ManagedOrder, OrderState


def test_managed_order_survives_restart(tmp_path):
    path = tmp_path / "trading.db"
    store = SQLiteStore(str(path))
    order = ManagedOrder("order-1")
    order.transition(OrderState.VALIDATED)
    order.transition(OrderState.RESERVED)
    store.save_managed_order(order)

    restarted = SQLiteStore(str(path))
    recovered = restarted.load_managed_order("order-1")
    assert recovered.order_id == "order-1"
    assert recovered.state == OrderState.RESERVED
    assert recovered.reason is None


def test_rejected_order_reason_survives_restart(tmp_path):
    path = tmp_path / "trading.db"
    store = SQLiteStore(str(path))
    order = ManagedOrder("order-2")
    order.transition(OrderState.REJECTED, reason="risk rejected")
    store.save_managed_order(order)

    recovered = SQLiteStore(str(path)).load_managed_order("order-2")
    assert recovered.state == OrderState.REJECTED
    assert recovered.reason == "risk rejected"
    assert recovered.terminal is True


def test_missing_managed_order_returns_none(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    assert store.load_managed_order("missing") is None
