from decimal import Decimal
from tempfile import TemporaryDirectory
from pathlib import Path

from app.trading.fill_accounting import FillAccounting
from app.trading.lifecycle import OrderLifecycleService
from app.trading.order_journal import OrderJournal
from app.trading.order_tracker import OrderTracker
from app.trading.position_snapshot import PositionSnapshotStore
from app.trading.risk import OrderRequest


class Execution:
    def __init__(self, submitted=True, order_id="paper-1"):
        self.submitted = submitted
        self.order_id = order_id

    def execute(self, order, client_order_id=None):
        if not self.submitted:
            return {
                "symbol": order.symbol,
                "submitted": False,
                "status": "DRY_RUN",
            }
        return {
            "symbol": order.symbol,
            "side": order.side,
            "submitted": True,
            "status": "accepted",
            "broker_order_id": self.order_id,
            "client_order_id": client_order_id,
        }


class Broker:
    def __init__(self, filled_qty="0.01"):
        self.filled_qty = filled_qty

    def get_order(self, order_id):
        return {
            "id": order_id,
            "symbol": "SPY",
            "side": "buy",
            "status": "filled",
            "filled_qty": self.filled_qty,
            "filled_avg_price": "770",
        }


order = OrderRequest(
    symbol="SPY",
    side="buy",
    quantity=Decimal("0.01"),
    estimated_price=Decimal("770"),
)

with TemporaryDirectory() as directory:
    root = Path(directory)
    journal = OrderJournal(root / "orders.json")
    positions = PositionSnapshotStore(root / "positions.json")
    service = OrderLifecycleService(
        Execution(),
        journal,
        OrderTracker(Broker()),
        FillAccounting(positions),
    )

    result = service.submit(order, "test-order-1")
    assert result["submitted"] is True
    assert result["status"] == "filled"
    assert result["filled_qty"] == "0.01"
    assert journal.get("paper-1")["status"] == "filled"
    assert positions.get("SPY") == Decimal("0.01")

with TemporaryDirectory() as directory:
    root = Path(directory)
    journal = OrderJournal(root / "orders.json")
    positions = PositionSnapshotStore(root / "positions.json")
    service = OrderLifecycleService(
        Execution(submitted=False),
        journal,
        OrderTracker(Broker()),
        FillAccounting(positions),
    )
    result = service.submit(order, "dry-run-1")
    assert result["submitted"] is False
    assert journal.all() == {}
    assert positions.get("SPY") is None

print("=== TRADING APP v2.0 / END-TO-END LIFECYCLE ===")
print("Simulated submission tracked: PASS")
print("Broker fill journaled: PASS")
print("Expected position updated: PASS")
print("Dry run creates no lifecycle state: PASS")
print("Real Alpaca API contacted: NO")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
