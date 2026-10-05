import tempfile
from decimal import Decimal
from pathlib import Path

from app.trading.order_journal import OrderJournal
from app.trading.order_tracker import OrderState
from app.trading.recovery import RecoveryManager


class FakeTracker:
    def get(self, order_id):
        return OrderState(
            order_id=order_id,
            symbol="SPY",
            side="buy",
            status="filled",
            filled_qty=Decimal("0.02"),
            filled_avg_price=Decimal("500"),
            terminal=True,
        )


print("=== TRADING APP v2.0 / RESTART RECOVERY ===")

with tempfile.TemporaryDirectory() as directory:
    journal = OrderJournal(Path(directory) / "orders.json")
    journal.record(OrderState(
        order_id="ORDER-1",
        symbol="SPY",
        side="buy",
        status="accepted",
        filled_qty=Decimal("0"),
        filled_avg_price=None,
        terminal=False,
    ))

    result = RecoveryManager(FakeTracker(), journal).reconcile_open_orders()

    assert result.checked == 1
    assert result.updated == 1
    assert result.terminal == 1
    assert result.open == 0
    assert journal.get("ORDER-1")["status"] == "filled"

    print("Persisted open order discovered: PASS")
    print("Broker state refreshed: PASS")
    print("Accepted-to-filled transition recovered: PASS")
    print("Terminal order removed from open set: PASS")

print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
