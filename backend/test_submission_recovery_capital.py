from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from app.trading.capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from app.trading.submission_ledger import SubmissionLedger
from app.trading.submission_recovery import SubmissionRecovery


class Broker:
    def __init__(self, status):
        self.status = status
        self.calls = 0
    def get_order_by_client_id(self, client_order_id):
        self.calls += 1
        return {"id": "broker-1", "status": self.status}
    def submit_order(self, payload):
        raise AssertionError("Recovery must never submit an order.")


with TemporaryDirectory() as d:
    capital = PortfolioCapitalCoordinator(
        CapitalConfig(Decimal("50000"), Decimal("5000")),
        Path(d) / "capital.json",
    )
    ledger = SubmissionLedger(Path(d) / "ledger.json")
    ledger.reserve("client-1", "fingerprint")
    capital.reserve("client-1", Decimal("500"), Decimal("50000"))

    open_broker = Broker("accepted")
    result = SubmissionRecovery(open_broker, ledger, capital).resolve("client-1")
    assert result["capital_released"] is False
    assert capital.get("client-1") == Decimal("500")
    assert open_broker.calls == 1

    terminal_broker = Broker("filled")
    result = SubmissionRecovery(terminal_broker, ledger, capital).resolve("client-1")
    assert result["capital_released"] is True
    assert capital.get("client-1") == Decimal("0")
    assert terminal_broker.calls == 1

with TemporaryDirectory() as d:
    capital = PortfolioCapitalCoordinator(
        CapitalConfig(Decimal("50000"), Decimal("5000")),
        Path(d) / "capital.json",
    )
    ledger = SubmissionLedger(Path(d) / "ledger.json")
    ledger.reserve("client-missing-capital", "fingerprint")
    try:
        SubmissionRecovery(Broker("filled"), ledger, capital).resolve(
            "client-missing-capital"
        )
        raise AssertionError("Missing capital reservation must fail closed.")
    except RuntimeError:
        pass

print("=== AMBIGUOUS SUBMISSION CAPITAL RECOVERY ===")
print("Open broker order retains capital: PASS")
print("Terminal broker order releases capital: PASS")
print("Missing capital state fails closed: PASS")
print("Read-only lookup only: PASS")
print("Automatic resubmission: NO")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
