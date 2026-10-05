from decimal import Decimal

import pytest

from app.storage import SQLiteStore
from app.trading.order_state import ManagedOrder, OrderState
from app.trading.resources import DurableResourceCoordinator
from app.trading.risk import OrderRequest
from app.trading.settlement import ExposureSettlement, SettlementRejected


def setup(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    resources = DurableResourceCoordinator(
        store, Decimal("50000"), Decimal("100000")
    )
    return store, resources, ExposureSettlement(resources)


def request(side):
    return OrderRequest("SPY", side, Decimal("1"), Decimal("100"))


def filled(order_id):
    order = ManagedOrder(order_id)
    for state in (
        OrderState.VALIDATED,
        OrderState.RESERVED,
        OrderState.SUBMITTED,
        OrderState.ACKNOWLEDGED,
        OrderState.FILLED,
    ):
        order.transition(state)
    return order


def test_sell_cannot_release_exposure_before_fill(tmp_path):
    store, resources, settlement = setup(tmp_path)
    resources.reserve_symbol_exposure("bot-1", "SPY", Decimal("500"))
    order = ManagedOrder("sell-1")
    order.transition(OrderState.VALIDATED)
    order.transition(OrderState.RESERVED)

    with pytest.raises(SettlementRejected, match="FILLED"):
        settlement.settle_sell(order, "bot-1", request("sell"))

    assert store.load_exposure_reservations("SPY") == {"bot-1": "500"}


def test_filled_sell_releases_exposure(tmp_path):
    store, resources, settlement = setup(tmp_path)
    resources.reserve_symbol_exposure("bot-1", "SPY", Decimal("500"))
    settlement.settle_sell(filled("sell-1"), "bot-1", request("sell"))
    assert store.load_exposure_reservations("SPY") == {"bot-1": "400"}


def test_filled_buy_adds_exposure(tmp_path):
    store, resources, settlement = setup(tmp_path)
    settlement.settle_buy(filled("buy-1"), "bot-1", request("buy"))
    assert store.load_exposure_reservations("SPY") == {"bot-1": "100"}
