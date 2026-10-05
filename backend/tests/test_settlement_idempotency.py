from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.order_state import ManagedOrder, OrderState
from app.trading.resources import DurableResourceCoordinator
from app.trading.risk import OrderRequest
from app.trading.settlement import ExposureSettlement


def test_repeated_filled_sell_has_one_financial_effect(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    resources = DurableResourceCoordinator(
        store, Decimal("50000"), Decimal("100000")
    )
    resources.reserve_symbol_exposure("bot-1", "SPY", Decimal("200"))
    settlement = ExposureSettlement(resources)
    order = ManagedOrder("sell-1", state=OrderState.FILLED)
    request = OrderRequest("SPY", "sell", Decimal("1"), Decimal("100"))

    assert settlement.settle_sell(order, "bot-1", request) is True
    assert settlement.settle_sell(order, "bot-1", request) is False
    assert store.load_exposure_reservations("SPY") == {"bot-1": "100"}
    assert store.load_order_settlement("sell-1") == "FILLED_SELL"


def test_failed_atomic_sell_does_not_claim_settlement(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    resources = DurableResourceCoordinator(
        store, Decimal("50000"), Decimal("100000")
    )
    resources.reserve_symbol_exposure("bot-1", "SPY", Decimal("50"))
    settlement = ExposureSettlement(resources)
    order = ManagedOrder("sell-too-large", state=OrderState.FILLED)
    request = OrderRequest("SPY", "sell", Decimal("1"), Decimal("100"))

    try:
        settlement.settle_sell(order, "bot-1", request)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected oversized settlement to fail.")

    assert store.load_order_settlement("sell-too-large") is None
    assert store.load_exposure_reservations("SPY") == {"bot-1": "50"}
