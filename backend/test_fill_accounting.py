from decimal import Decimal
from tempfile import TemporaryDirectory
from pathlib import Path

from app.trading.fill_accounting import FillAccounting
from app.trading.order_tracker import OrderState
from app.trading.position_reconciler import PositionMismatch
from app.trading.position_snapshot import PositionSnapshotStore


def state(side, qty):
    return OrderState(
        order_id="order-1",
        symbol="SPY",
        side=side,
        status="filled",
        filled_qty=Decimal(qty),
        filled_avg_price=Decimal("770"),
        terminal=True,
    )


with TemporaryDirectory() as directory:
    store = PositionSnapshotStore(Path(directory) / "positions.json")
    accounting = FillAccounting(store)

    assert accounting.apply(state("buy", "0.02")) == Decimal("0.02")
    assert store.get("SPY") == Decimal("0.02")

    assert accounting.apply(state("sell", "0.005")) == Decimal("0.015")
    assert store.get("SPY") == Decimal("0.015")

    try:
        accounting.apply(state("sell", "0.02"))
        raise AssertionError("Oversell must fail closed.")
    except PositionMismatch:
        pass

    assert store.get("SPY") == Decimal("0.015")

print("=== TRADING APP v2.0 / FILL ACCOUNTING ===")
print("Buy fill increases expected position: PASS")
print("Sell fill decreases expected position: PASS")
print("Oversell rejected before persistence: PASS")
print("Expected position preserved after rejection: PASS")
print("Broker interaction: NO")
print("RESULT: PASS")
