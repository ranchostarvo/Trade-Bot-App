import tempfile
from decimal import Decimal
from pathlib import Path

from app.trading.fill_accounting import FillAccounting
from app.trading.order_tracker import OrderState
from app.trading.position_snapshot import PositionSnapshotStore

with tempfile.TemporaryDirectory() as root:
    store = PositionSnapshotStore(Path(root) / "positions.json")
    accounting = FillAccounting(store)

    partial = OrderState(
        "order-1", "SPY", "buy", "partially_filled",
        Decimal("0.4"), Decimal("500"), False,
    )
    assert accounting.apply(partial) == Decimal("0.4")
    assert accounting.apply(partial) == Decimal("0.4")

    filled = OrderState(
        "order-1", "SPY", "buy", "filled",
        Decimal("1"), Decimal("501"), True,
    )
    assert accounting.apply(filled) == Decimal("1")
    assert accounting.apply(filled) == Decimal("1")

    # Restart and replay must remain idempotent.
    restarted = FillAccounting(
        PositionSnapshotStore(Path(root) / "positions.json")
    )
    assert restarted.apply(filled) == Decimal("1")

print("ATOMIC IMMEDIATE FILL ACCOUNTING: PASS")
print("Duplicate partial observation: IDEMPOTENT")
print("Cumulative fill delta: PASS")
print("Restart replay: IDEMPOTENT")
print("Real Alpaca order submitted: NO")
