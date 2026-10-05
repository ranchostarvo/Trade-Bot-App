from decimal import Decimal

from app.trading.position_reconciler import (
    PositionMismatch,
    PositionReconciler,
)


class FakeBroker:
    def __init__(self, qty):
        self.qty = qty

    def get_position(self, symbol):
        return {
            "symbol": symbol,
            "qty": str(self.qty),
            "avg_entry_price": "500",
            "market_value": "10",
        }


print("=== TRADING APP v2.0 / POSITION RECONCILIATION ===")

reconciler = PositionReconciler(FakeBroker("0.02"))
position = reconciler.reconcile_minimum_fill(
    "SPY",
    Decimal("0.02"),
)
assert position.symbol == "SPY"
assert position.quantity == Decimal("0.02")
print("Broker position parsed: PASS")
print("Expected filled quantity reconciled: PASS")

try:
    PositionReconciler(FakeBroker("0.01")).reconcile_minimum_fill(
        "SPY",
        Decimal("0.02"),
    )
    raise AssertionError("Position mismatch was not detected.")
except PositionMismatch:
    print("Position mismatch detected: PASS")

print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
