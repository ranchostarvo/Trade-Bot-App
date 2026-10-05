from decimal import Decimal

from app.trading.capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from app.trading.execution import ExecutionEngine
from app.trading.risk import AccountRiskState, OrderRequest, RiskConfig, RiskEngine, RiskRejected
from app.trading.submission_ledger import SubmissionLedger
from pathlib import Path
from tempfile import TemporaryDirectory


class Kill:
    def validate(self): pass
class Account:
    def get_risk_state(self):
        return AccountRiskState(Decimal("100000"), Decimal("100000"))
class Session:
    def validate(self): pass
class AmbiguousBroker:
    def submit_order(self, payload):
        raise TimeoutError("simulated timeout after transmission")


with TemporaryDirectory() as d:
    capital = PortfolioCapitalCoordinator(
        CapitalConfig(Decimal("50000"), Decimal("5000")),
        Path(d) / "capital.json",
    )
    ledger = SubmissionLedger(Path(d) / "ledger.json")
    engine = ExecutionEngine(
        risk_engine=RiskEngine(RiskConfig(
            max_order_notional=Decimal("500"),
            max_daily_loss_pct=Decimal("2.5"),
            trading_enabled=True,
            dry_run=False,
        )),
        kill_switch=Kill(),
        account_state_provider=Account(),
        broker=AmbiguousBroker(),
        submission_ledger=ledger,
        session_guard=Session(),
        capital_coordinator=capital,
        available_cash_provider=lambda: Decimal("50000"),
    )
    order = OrderRequest("SPY", "buy", Decimal("1"), Decimal("100"))
    try:
        engine.execute(order, client_order_id="ambiguous-1")
        raise AssertionError("Ambiguous broker outcome must fail closed.")
    except RiskRejected as exc:
        assert "ambiguous" in str(exc).lower()

    assert capital.get("ambiguous-1") == Decimal("100")
    assert ledger.get("ambiguous-1") is not None

    # Restart: capital must remain unavailable until broker reconciliation.
    restarted = PortfolioCapitalCoordinator(
        CapitalConfig(Decimal("50000"), Decimal("5000")),
        Path(d) / "capital.json",
    )
    assert restarted.get("ambiguous-1") == Decimal("100")

print("=== AMBIGUOUS BROKER TRANSMISSION ===")
print("Execution fails closed: PASS")
print("Capital reservation retained: PASS")
print("Idempotency reservation retained: PASS")
print("Reservation survives restart: PASS")
print("Automatic resubmission: NO")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
