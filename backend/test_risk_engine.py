from decimal import Decimal

from app.trading.execution import ExecutionEngine
from app.trading.risk import OrderRequest, RiskRejected


engine = ExecutionEngine()

print("=== TRADING APP v2.0 / RISK TEST ===")

safe = OrderRequest(
    symbol="SPY",
    side="buy",
    quantity=Decimal("1"),
    estimated_price=Decimal("400"),
)

result = engine.execute(safe)

assert result["approved"] is True
assert result["submitted"] is False
assert result["status"] == "DRY_RUN"

print("Safe order validation: PASS")
print("Broker submission blocked: PASS")
print("Dry-run interlock: PASS")

oversized = OrderRequest(
    symbol="SPY",
    side="buy",
    quantity=Decimal("2"),
    estimated_price=Decimal("400"),
)

try:
    engine.execute(oversized)
    raise AssertionError("Oversized order was not rejected.")
except RiskRejected:
    print("Maximum-order protection: PASS")

print("RESULT: PASS")
