from decimal import Decimal

from app.trading.order_tracker import OrderTracker


class FakeBroker:
    def __init__(self, status, filled_qty="0", filled_avg_price=None):
        self.status = status
        self.filled_qty = filled_qty
        self.filled_avg_price = filled_avg_price
        self.calls = []

    def get_order(self, order_id):
        self.calls.append(order_id)
        return {
            "id": order_id,
            "symbol": "SPY",
            "side": "buy",
            "status": self.status,
            "filled_qty": self.filled_qty,
            "filled_avg_price": self.filled_avg_price,
        }


print("=== TRADING APP v2.0 / ORDER TRACKER ===")

accepted = OrderTracker(FakeBroker("accepted")).get("ORDER-1")
assert accepted.status == "accepted"
assert accepted.terminal is False
assert accepted.filled_qty == Decimal("0")
print("Accepted order remains open: PASS")

partial = OrderTracker(
    FakeBroker("partially_filled", "0.01", "500")
).get("ORDER-2")
assert partial.terminal is False
assert partial.filled_qty == Decimal("0.01")
assert partial.filled_avg_price == Decimal("500")
print("Partial fill tracked: PASS")

filled = OrderTracker(
    FakeBroker("filled", "0.02", "500")
).get("ORDER-3")
assert filled.terminal is True
print("Filled order recognized as terminal: PASS")

for status in ("canceled", "expired", "rejected"):
    state = OrderTracker(FakeBroker(status)).get("ORDER-X")
    assert state.terminal is True
print("Failure terminal states recognized: PASS")

print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
