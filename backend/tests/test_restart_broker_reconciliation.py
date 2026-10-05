from decimal import Decimal

import pytest

from app.storage import SQLiteStore
from app.trading.broker_orders import BrokerOrderReconciler
from app.trading.kill_switch import KillSwitch
from app.trading.order_state import ManagedOrder, OrderState
from app.trading.resources import DurableResourceCoordinator
from app.trading.restart_reconciliation import (
    RestartBrokerReconciliation,
    RestartReconciliationBlocked,
)
from app.trading.settlement import ExposureSettlement


class FakeBroker:
    def __init__(self, status):
        self.status = status
        self.requested = []

    def order_status(self, order_id):
        self.requested.append(order_id)
        if isinstance(self.status, Exception):
            raise self.status
        return self.status


def submitted(store, order_id):
    order = ManagedOrder(order_id)
    for state in (OrderState.VALIDATED, OrderState.RESERVED, OrderState.SUBMITTED):
        order.transition(state)
    store.save_managed_order(order)


def build(tmp_path, status):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    resources = DurableResourceCoordinator(
        store, Decimal("50000"), Decimal("100000")
    )
    switch = KillSwitch()
    broker = FakeBroker(status)
    reconciler = BrokerOrderReconciler(store, ExposureSettlement(resources))
    service = RestartBrokerReconciliation(
        store, broker, reconciler, switch
    )
    return store, resources, switch, broker, service


def save_context(store, broker_order_id="broker-123"):
    store.save_order_recovery_context(
        "order-1", "bot-1", "SPY", "buy", "1", "100", broker_order_id
    )


def test_restart_reconstructs_and_reconciles_filled_buy(tmp_path):
    store, resources, switch, broker, service = build(tmp_path, "filled")
    submitted(store, "order-1")
    save_context(store)
    resources.reserve_pending_exposure(
        "order-1", "bot-1", "SPY", Decimal("100")
    )
    assert service.reconcile() == []
    assert broker.requested == ["broker-123"]
    assert store.load_managed_order("order-1").state is OrderState.FILLED
    assert store.load_pending_exposure() == {}
    assert switch.engaged is True


def test_restart_broker_failure_stays_blocked(tmp_path):
    store, resources, switch, broker, service = build(
        tmp_path, RuntimeError("broker unavailable")
    )
    submitted(store, "order-1")
    save_context(store)
    resources.reserve_pending_exposure(
        "order-1", "bot-1", "SPY", Decimal("100")
    )
    with pytest.raises(RestartReconciliationBlocked):
        service.reconcile()
    assert store.load_managed_order("order-1").state is OrderState.SUBMITTED
    assert "order-1" in store.load_pending_exposure()
    assert switch.engaged is True


def test_restart_missing_context_stays_blocked(tmp_path):
    store, resources, switch, broker, service = build(tmp_path, "filled")
    submitted(store, "order-1")
    with pytest.raises(RestartReconciliationBlocked, match="missing-context"):
        service.reconcile()
    assert switch.engaged is True


def test_restart_missing_broker_order_id_stays_blocked(tmp_path):
    store, resources, switch, broker, service = build(tmp_path, "filled")
    submitted(store, "order-1")
    save_context(store, None)
    with pytest.raises(
        RestartReconciliationBlocked, match="missing-broker-order-id"
    ):
        service.reconcile()
    assert broker.requested == []
    assert switch.engaged is True
