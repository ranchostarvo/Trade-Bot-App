from decimal import Decimal

from app.trading.execution import ExecutionEngine
from app.trading.risk import (
    AccountRiskState,
    OrderRequest,
)


class TestAccountProvider:
    def get_risk_state(self):
        return AccountRiskState(
            start_of_day_equity=Decimal("100000"),
            current_equity=Decimal("100000"),
        )


class BrokerThatMustNotRun:
    def submit_order(self, payload):
        raise AssertionError(
            "Broker was called while dry-run was active."
        )


print(
    "=== TRADING APP v2.0 / "
    "EXECUTION BROKER GATE ==="
)

engine = ExecutionEngine(
    account_state_provider=TestAccountProvider(),
    broker=BrokerThatMustNotRun(),
)

order = OrderRequest(
    symbol="SPY",
    side="buy",
    quantity=Decimal("1"),
    estimated_price=Decimal("400"),
)

result = engine.execute(order)

assert result["approved"] is True
assert result["submitted"] is False
assert result["status"] == "DRY_RUN"

print("Risk pipeline passed: PASS")
print("Dry-run gate remained active: PASS")
print("Broker was not called: PASS")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
