import pytest

from app.storage import SQLiteStore
from app.trading.kill_switch import KillSwitch
from app.trading.order_recovery import OrderRecoveryBlocked, UnresolvedOrderRecovery
from app.trading.order_state import ManagedOrder, OrderState


def save_at(store, order_id, states):
    order = ManagedOrder(order_id)
    for state in states:
        order.transition(state)
    store.save_managed_order(order)


def test_restart_engages_kill_switch_for_submitted_order(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    save_at(store, "order-1", [
        OrderState.VALIDATED, OrderState.RESERVED, OrderState.SUBMITTED
    ])
    switch = KillSwitch()
    recovery = UnresolvedOrderRecovery(store, switch)
    with pytest.raises(OrderRecoveryBlocked, match="order-1:SUBMITTED"):
        recovery.assert_clear()
    assert switch.engaged is True


def test_acknowledged_order_is_also_unresolved(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    save_at(store, "order-1", [
        OrderState.VALIDATED, OrderState.RESERVED,
        OrderState.SUBMITTED, OrderState.ACKNOWLEDGED
    ])
    assert [o.state for o in store.load_unresolved_orders()] == [
        OrderState.ACKNOWLEDGED
    ]


def test_no_unresolved_orders_allows_startup(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    switch = KillSwitch()
    assert UnresolvedOrderRecovery(store, switch).assert_clear() is True
    assert switch.engaged is False
