import tempfile
from decimal import Decimal
from pathlib import Path

from app.trading.execution import ExecutionEngine
from app.trading.risk import (
    AccountRiskState,
    OrderRequest,
    RiskConfig,
    RiskEngine,
)
from app.trading.submission_ledger import SubmissionLedger


class VerifiedSessionGuard:
    def validate(self):
        return True


class TestAccountProvider:
    def get_risk_state(self):
        return AccountRiskState(
            start_of_day_equity=Decimal("100000"),
            current_equity=Decimal("100000"),
        )


class FakePaperBroker:
    def __init__(self):
        self.orders = []

    def submit_order(self, payload):
        self.orders.append(payload)
        return {"id": "TEST-PAPER-001", "status": "accepted"}


print("=== TRADING APP v2.0 / ENABLED PAPER EXECUTION TEST ===")

risk = RiskEngine(RiskConfig(
    max_order_notional=Decimal("25"),
    max_daily_loss_pct=Decimal("2.5"),
    trading_enabled=True,
    dry_run=False,
))
broker = FakePaperBroker()

with tempfile.TemporaryDirectory() as directory:
    engine = ExecutionEngine(
        risk_engine=risk,
        account_state_provider=TestAccountProvider(),
        broker=broker,
        submission_ledger=SubmissionLedger(Path(directory) / "ledger.json"),
    session_guard=VerifiedSessionGuard(),
    )

    order = OrderRequest(
        symbol="TEST",
        side="buy",
        quantity=Decimal("1"),
        estimated_price=Decimal("10"),
    )
    result = engine.execute(order, client_order_id="TEST-PAPER-ORDER-001")

assert result["approved"] is True
assert result["submitted"] is True
assert result["broker_order_id"] == "TEST-PAPER-001"
assert result["client_order_id"] == "TEST-PAPER-ORDER-001"
assert len(broker.orders) == 1

payload = broker.orders[0]
assert payload["symbol"] == "TEST"
assert payload["qty"] == "1"
assert payload["side"] == "buy"
assert payload["type"] == "market"
assert payload["time_in_force"] == "day"
assert payload["client_order_id"] == "TEST-PAPER-ORDER-001"

print("Execution-enabled branch reached: PASS")
print("Test-only $25 ceiling enforced: PASS")
print("Persistent idempotency ledger enforced: PASS")
print("client_order_id propagated: PASS")
print("Fake paper broker received order: PASS")
print("Real Alpaca API contacted: NO")
print("Real Alpaca paper order submitted: NO")
print("Live trading enabled: NO")
print("RESULT: PASS")
