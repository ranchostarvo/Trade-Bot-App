from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.order_state import ManagedOrder, OrderState
from app.trading.resources import DurableResourceCoordinator
from app.trading.settlement import ExposureSettlement


def resources(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    return store, DurableResourceCoordinator(
        store, Decimal("50000"), Decimal("100000")
    )


def test_filled_buy_settlement_is_idempotent(tmp_path):
    store, res = resources(tmp_path)
    res.reserve_pending_exposure(
        "buy-1", "bot-1", "SPY", Decimal("100")
    )
    settlement = ExposureSettlement(res)
    order = ManagedOrder("buy-1", state=OrderState.FILLED)

    assert settlement.settle_buy(order, "bot-1", None) is True
    assert settlement.settle_buy(order, "bot-1", None) is False
    assert store.load_exposure_reservations("SPY") == {"bot-1": "100"}
    assert store.load_order_settlement("buy-1") == "FILLED_BUY"


def test_rejected_pending_cleanup_is_idempotent(tmp_path):
    store, res = resources(tmp_path)
    res.reserve_pending_exposure(
        "buy-rejected", "bot-1", "SPY", Decimal("100")
    )
    settlement = ExposureSettlement(res)
    order = ManagedOrder("buy-rejected", state=OrderState.REJECTED)

    assert settlement.settle_terminal(order) is True
    assert settlement.settle_terminal(order) is False
    assert store.load_pending_exposure() == {}
    assert store.load_order_settlement("buy-rejected") == "REJECTED"
