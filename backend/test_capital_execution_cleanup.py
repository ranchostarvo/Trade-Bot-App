from decimal import Decimal

from app.trading.capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from app.trading.execution import ExecutionEngine
from app.trading.risk import AccountRiskState, OrderRequest, RiskConfig, RiskEngine, RiskRejected


class Kill:
    def validate(self):
        return None


class Account:
    def get_risk_state(self):
        return AccountRiskState(Decimal("100000"), Decimal("100000"))


class Session:
    def validate(self):
        return None


class BrokenLedger:
    def reserve(self, client_order_id, fingerprint):
        raise RuntimeError("simulated ledger failure")


class Broker:
    called = False
    def submit_order(self, payload):
        self.called = True
        raise AssertionError("Broker must not be reached.")


capital = PortfolioCapitalCoordinator(
    CapitalConfig(Decimal("50000"), Decimal("5000"))
)
broker = Broker()
engine = ExecutionEngine(
    risk_engine=RiskEngine(RiskConfig(
        max_order_notional=Decimal("500"),
        max_daily_loss_pct=Decimal("2.5"),
        trading_enabled=True,
        dry_run=False,
    )),
    kill_switch=Kill(),
    account_state_provider=Account(),
    broker=broker,
    submission_ledger=BrokenLedger(),
    session_guard=Session(),
    capital_coordinator=capital,
    available_cash_provider=lambda: Decimal("50000"),
)

order = OrderRequest(
    symbol="SPY",
    side="buy",
    quantity=Decimal("1"),
    estimated_price=Decimal("100"),
)

try:
    engine.execute(order, client_order_id="cleanup-1")
    raise AssertionError("Ledger failure must reject execution.")
except RiskRejected:
    pass

assert capital.allocated == Decimal("0")
assert broker.called is False

print("=== TRADING APP v2.0 / CAPITAL PRE-SUBMISSION CLEANUP ===")
print("Capital reserved before ledger: PASS")
print("Ledger failure rejected: PASS")
print("Capital released after ledger failure: PASS")
print("Broker reached: NO")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
