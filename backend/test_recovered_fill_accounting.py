from decimal import Decimal
from tempfile import TemporaryDirectory
from pathlib import Path

from app.trading.fill_accounting import FillAccounting
from app.trading.order_journal import OrderJournal
from app.trading.order_tracker import OrderState
from app.trading.position_snapshot import PositionSnapshotStore
from app.trading.recovery import RecoveryManager


class Tracker:
    def __init__(self, state):
        self.state = state

    def get(self, order_id):
        return self.state


def state(status, qty, terminal=False):
    return OrderState(
        order_id="order-1",
        symbol="SPY",
        side="buy",
        status=status,
        filled_qty=Decimal(qty),
        filled_avg_price=Decimal("770") if Decimal(qty) else None,
        terminal=terminal,
    )


with TemporaryDirectory() as directory:
    root = Path(directory)
    journal = OrderJournal(root / "orders.json")
    positions = PositionSnapshotStore(root / "positions.json")
    accounting = FillAccounting(positions)

    journal.record(state("partially_filled", "0.01"))
    positions.set("SPY", Decimal("0.01"))

    manager = RecoveryManager(
        Tracker(state("filled", "0.02", True)),
        journal,
        accounting,
    )
    result = manager.reconcile_open_orders()
    assert result.checked == 1
    assert result.updated == 1
    assert result.terminal == 1
    assert positions.get("SPY") == Decimal("0.02")

    # Terminal orders are no longer open, so a second restart cannot
    # apply the same fill again.
    again = RecoveryManager(
        Tracker(state("filled", "0.02", True)),
        journal,
        accounting,
    ).reconcile_open_orders()
    assert again.checked == 0
    assert positions.get("SPY") == Decimal("0.02")

with TemporaryDirectory() as directory:
    root = Path(directory)
    journal = OrderJournal(root / "orders.json")
    positions = PositionSnapshotStore(root / "positions.json")
    accounting = FillAccounting(positions)
    journal.record(state("partially_filled", "0.02"))
    positions.set("SPY", Decimal("0.02"))

    try:
        RecoveryManager(
            Tracker(state("partially_filled", "0.01")),
            journal,
            accounting,
        ).reconcile_open_orders()
        raise AssertionError("Regressed fill quantity must fail closed.")
    except RuntimeError:
        pass

    assert positions.get("SPY") == Decimal("0.02")

print("=== TRADING APP v2.0 / RECOVERED FILL ACCOUNTING ===")
print("Incremental recovered fill applied once: PASS")
print("Repeated restart does not double count: PASS")
print("Regressed fill quantity rejected: PASS")
print("Position preserved after rejection: PASS")
print("Broker write interaction: NO")
print("RESULT: PASS")
