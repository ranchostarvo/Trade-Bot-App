import tempfile
from decimal import Decimal
from pathlib import Path

from app.trading.order_journal import OrderJournal
from app.trading.order_tracker import OrderState

print("=== TRADING APP v2.0 / ORDER JOURNAL ===")

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "orders.json"
    journal = OrderJournal(path)

    accepted = OrderState(
        order_id="ORDER-1", symbol="SPY", side="buy",
        status="accepted", filled_qty=Decimal("0"),
        filled_avg_price=None, terminal=False,
    )
    journal.record(accepted)
    assert journal.get("ORDER-1")["status"] == "accepted"
    print("Accepted state persisted: PASS")

    filled = OrderState(
        order_id="ORDER-1", symbol="SPY", side="buy",
        status="filled", filled_qty=Decimal("0.02"),
        filled_avg_price=Decimal("500"), terminal=True,
    )
    journal.record(filled)
    saved = journal.get("ORDER-1")
    assert saved["status"] == "filled"
    assert saved["filled_qty"] == "0.02"
    assert saved["terminal"] is True
    print("Lifecycle update persisted: PASS")
    print("Terminal fill persisted: PASS")

print("Broker interaction: NO")
print("RESULT: PASS")
