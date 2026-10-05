from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from app.trading.fill_accounting import FillAccounting
from app.trading.order_journal import OrderJournal
from app.trading.order_tracker import OrderState
from app.trading.position_snapshot import PositionSnapshotStore
from app.trading.recovery import RecoveryManager


class Tracker:
    def __init__(self, states):
        self.states = states

    def get(self, order_id):
        return self.states[order_id]


def state(order_id, status, qty, terminal=False):
    return OrderState(
        order_id=order_id,
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

    journal.record(state("soak-1", "new", "0"))
    expected = Decimal("0")

    # Repeated restart/recovery cycles with cumulative broker fills.
    scenarios = [
        ("partially_filled", "0.01", False),
        ("partially_filled", "0.01", False),  # replay
        ("partially_filled", "0.02", False),
        ("partially_filled", "0.02", False),  # replay
        ("filled", "0.03", True),
    ]

    for status, qty, terminal in scenarios:
        broker_state = state("soak-1", status, qty, terminal)
        RecoveryManager(
            Tracker({"soak-1": broker_state}),
            journal,
            accounting,
        ).reconcile_open_orders()
        expected = Decimal(qty)
        assert positions.get("SPY") == expected

    # Terminal order disappears from open-order recovery on all later restarts.
    for _ in range(25):
        result = RecoveryManager(
            Tracker({"soak-1": state("soak-1", "filled", "0.03", True)}),
            journal,
            accounting,
        ).reconcile_open_orders()
        assert result.checked == 0
        assert positions.get("SPY") == Decimal("0.03")

print("=== TRADING APP v2.0 / RESTART SOAK ===")
print("Incremental cumulative fills: PASS")
print("Duplicate cumulative fills: PASS")
print("Terminal recovery: PASS")
print("25 repeated post-terminal restarts: PASS")
print("Expected position stable: PASS")
print("Broker writes: NONE")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
