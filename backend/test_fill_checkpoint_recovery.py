from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from app.trading.fill_accounting import FillAccounting
from app.trading.fill_checkpoint import FillCheckpointStore
from app.trading.order_journal import OrderJournal
from app.trading.order_tracker import OrderState, OrderTracker
from app.trading.position_snapshot import PositionSnapshotStore
from app.trading.recovery import RecoveryManager


class Broker:
    def get_order(self, order_id):
        return {
            "id": order_id,
            "symbol": "SPY",
            "side": "buy",
            "status": "partially_filled",
            "filled_qty": "0.02",
            "filled_avg_price": "770",
        }


with TemporaryDirectory() as directory:
    root = Path(directory)
    journal = OrderJournal(root / "orders.json")
    positions = PositionSnapshotStore(root / "positions.json")
    checkpoints = FillCheckpointStore(root / "fills.json")

    # Simulate an old journal record followed by successful fill accounting.
    journal.record(OrderState(
        order_id="paper-1",
        symbol="SPY",
        side="buy",
        status="partially_filled",
        filled_qty=Decimal("0.01"),
        filled_avg_price=Decimal("770"),
        terminal=False,
    ))
    positions.set("SPY", Decimal("0.02"))
    checkpoints.set("paper-1", Decimal("0.02"))

    # Simulate a crash before the order journal could be advanced to 0.02.
    # On restart the broker still reports 0.02. Recovery must NOT apply +0.01 again.
    recovery = RecoveryManager(
        OrderTracker(Broker()),
        journal,
        fill_accounting=FillAccounting(positions),
        fill_checkpoint_store=checkpoints,
    )
    result = recovery.reconcile_open_orders()

    assert result.checked == 1
    assert positions.get("SPY") == Decimal("0.02")
    assert checkpoints.get("paper-1") == Decimal("0.02")
    assert Decimal(str(journal.get("paper-1")["filled_qty"])) == Decimal("0.02")

print("=== TRADING APP v2.0 / CRASH RECOVERY IDEMPOTENCY ===")
print("Stale journal simulated: PASS")
print("Accounted fill checkpoint preserved: PASS")
print("Fill not double-counted after restart: PASS")
print("Journal caught up to broker state: PASS")
print("Broker write performed: NO")
print("Real Alpaca API contacted: NO")
print("RESULT: PASS")
