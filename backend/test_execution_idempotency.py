import tempfile
from decimal import Decimal
from pathlib import Path

from app.trading.execution import ExecutionEngine
from app.trading.risk import AccountRiskState, OrderRequest, RiskConfig, RiskEngine, RiskRejected
from app.trading.submission_ledger import SubmissionLedger


class VerifiedSessionGuard:
    def validate(self):
        return True


class AccountProvider:
    def get_risk_state(self):
        return AccountRiskState(
            start_of_day_equity=Decimal("100000"),
            current_equity=Decimal("100000"),
        )


class FakeBroker:
    def __init__(self):
        self.calls = 0
        self.payload = None

    def submit_order(self, payload):
        self.calls += 1
        self.payload = payload
        return {"id": "BROKER-1", "status": "accepted"}


print("=== TRADING APP v2.0 / EXECUTION IDEMPOTENCY ===")

with tempfile.TemporaryDirectory() as directory:
    broker = FakeBroker()
    engine = ExecutionEngine(
        risk_engine=RiskEngine(RiskConfig(
            max_order_notional=Decimal("500"),
            max_daily_loss_pct=Decimal("2.5"),
            trading_enabled=True,
            dry_run=False,
        )),
        account_state_provider=AccountProvider(),
        broker=broker,
        submission_ledger=SubmissionLedger(Path(directory) / "ledger.json"),
    session_guard=VerifiedSessionGuard(),
    )
    order = OrderRequest(
        symbol="SPY",
        side="buy",
        quantity=Decimal("0.02"),
        estimated_price=Decimal("500"),
    )

    result = engine.execute(order, client_order_id="BOT-1-ORDER-1")
    assert result["submitted"] is True
    assert broker.calls == 1
    assert broker.payload["client_order_id"] == "BOT-1-ORDER-1"
    print("First fake submission allowed: PASS")
    print("client_order_id passed to broker: PASS")

    try:
        engine.execute(order, client_order_id="BOT-1-ORDER-1")
        raise AssertionError("Duplicate execution was not blocked.")
    except RiskRejected:
        assert broker.calls == 1
        print("Duplicate execution blocked before broker: PASS")

print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
