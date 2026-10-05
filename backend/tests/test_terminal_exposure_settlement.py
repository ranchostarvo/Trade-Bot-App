from decimal import Decimal

import pytest

from app.storage import SQLiteStore
from app.trading.order_state import ManagedOrder, OrderState
from app.trading.resources import DurableResourceCoordinator
from app.trading.settlement import ExposureSettlement, SettlementRejected


def setup(tmp_path, order_id="order-1"):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    resources = DurableResourceCoordinator(
        store, Decimal("50000"), Decimal("100000")
    )
    resources.reserve_pending_exposure(
        order_id, "bot-1", "SPY", Decimal("100")
    )
    return store, ExposureSettlement(resources)


def test_rejected_order_releases_pending_exposure(tmp_path):
    store, settlement = setup(tmp_path)
    order = ManagedOrder("order-1")
    order.transition(OrderState.REJECTED, reason="broker rejected")
    settlement.settle_terminal(order)
    assert store.load_pending_exposure() == {}


def test_canceled_order_releases_pending_exposure(tmp_path):
    store, settlement = setup(tmp_path)
    order = ManagedOrder("order-1")
    order.transition(OrderState.VALIDATED)
    order.transition(OrderState.RESERVED)
    order.transition(OrderState.CANCELED)
    settlement.settle_terminal(order)
    assert store.load_pending_exposure() == {}


def test_nonterminal_order_cannot_release_pending_exposure(tmp_path):
    store, settlement = setup(tmp_path)
    order = ManagedOrder("order-1")
    order.transition(OrderState.VALIDATED)
    order.transition(OrderState.RESERVED)
    order.transition(OrderState.SUBMITTED)

    with pytest.raises(SettlementRejected, match="REJECTED or CANCELED"):
        settlement.settle_terminal(order)

    assert "order-1" in store.load_pending_exposure()
