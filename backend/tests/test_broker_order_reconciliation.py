from decimal import Decimal

import pytest

from app.storage import SQLiteStore
from app.trading.broker_orders import BrokerOrderReconciler, BrokerOrderStateRejected
from app.trading.order_state import ManagedOrder, OrderState
from app.trading.resources import DurableResourceCoordinator
from app.trading.risk import OrderRequest
from app.trading.settlement import ExposureSettlement


def setup(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    resources = DurableResourceCoordinator(
        store, Decimal("50000"), Decimal("100000")
    )
    settlement = ExposureSettlement(resources)
    return store, resources, BrokerOrderReconciler(store, settlement)


def submitted(store, order_id):
    order = ManagedOrder(order_id)
    for state in (OrderState.VALIDATED, OrderState.RESERVED, OrderState.SUBMITTED):
        order.transition(state)
    store.save_managed_order(order)


def buy():
    return OrderRequest("SPY", "buy", Decimal("1"), Decimal("100"))


def test_filled_buy_converts_pending_exposure(tmp_path):
    store, resources, reconciler = setup(tmp_path)
    submitted(store, "order-1")
    resources.reserve_pending_exposure("order-1", "bot-1", "SPY", Decimal("100"))
    order = reconciler.reconcile("order-1", "filled", "bot-1", buy())
    assert order.state is OrderState.FILLED
    assert store.load_pending_exposure() == {}
    assert store.load_exposure_reservations("SPY") == {"bot-1": "100"}


def test_rejected_buy_releases_pending_exposure(tmp_path):
    store, resources, reconciler = setup(tmp_path)
    submitted(store, "order-1")
    resources.reserve_pending_exposure("order-1", "bot-1", "SPY", Decimal("100"))
    order = reconciler.reconcile("order-1", "rejected", "bot-1", buy())
    assert order.state is OrderState.REJECTED
    assert store.load_pending_exposure() == {}


def test_unknown_broker_status_fails_closed(tmp_path):
    store, resources, reconciler = setup(tmp_path)
    submitted(store, "order-1")
    resources.reserve_pending_exposure("order-1", "bot-1", "SPY", Decimal("100"))
    with pytest.raises(BrokerOrderStateRejected, match="Unsupported"):
        reconciler.reconcile("order-1", "mystery", "bot-1", buy())
    assert store.load_managed_order("order-1").state is OrderState.SUBMITTED
    assert "order-1" in store.load_pending_exposure()
