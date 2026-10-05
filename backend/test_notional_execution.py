import tempfile
from decimal import Decimal
from pathlib import Path

from app.trading.execution import ExecutionEngine
from app.trading.risk import AccountRiskState, OrderRequest, RiskConfig, RiskEngine, RiskRejected
from app.trading.submission_ledger import SubmissionLedger


class Account:
    def get_risk_state(self):
        return AccountRiskState(Decimal("100000"), Decimal("100000"))


class FakeBroker:
    def __init__(self):
        self.orders = []

    def submit_order(self, payload):
        self.orders.append(payload)
        return {"id": "NOTIONAL-001", "status": "accepted"}


risk = RiskEngine(RiskConfig(
    max_order_notional=Decimal("25"),
    trading_enabled=True,
    dry_run=False,
))
broker = FakeBroker()

with tempfile.TemporaryDirectory() as directory:
    engine = ExecutionEngine(
        risk_engine=risk,
        account_state_provider=Account(),
        broker=broker,
        submission_ledger=SubmissionLedger(Path(directory) / "ledger.json"),
    )

    order = OrderRequest(
        symbol="SPY",
        side="buy",
        quantity=Decimal("0"),
        estimated_price=Decimal("770"),
        requested_notional=Decimal("10"),
    )
    result = engine.execute(order, client_order_id="NOTIONAL-TEST-001")

    assert result["submitted"] is True
    assert result["notional"] == "10"
    assert broker.orders[0]["notional"] == "10"
    assert "qty" not in broker.orders[0]

    try:
        engine.execute(
            OrderRequest("SPY", "buy", Decimal("1"), Decimal("10"), Decimal("10")),
            client_order_id="AMBIGUOUS-001",
        )
        raise AssertionError("Ambiguous sizing must fail.")
    except RiskRejected:
        pass

    try:
        engine.execute(
            OrderRequest("SPY", "buy", Decimal("0"), Decimal("770"), Decimal("26")),
            client_order_id="TOO-LARGE-001",
        )
        raise AssertionError("Notional ceiling must fail.")
    except RiskRejected:
        pass

assert len(broker.orders) == 1
print("=== TRADING APP v2.0 / NOTIONAL EXECUTION ===")
print("$10 notional risk validation: PASS")
print("Notional broker payload: PASS")
print("Quantity omitted for notional order: PASS")
print("Ambiguous sizing rejected: PASS")
print("$25 test ceiling enforced: PASS")
print("Real Alpaca API contacted: NO")
print("RESULT: PASS")
