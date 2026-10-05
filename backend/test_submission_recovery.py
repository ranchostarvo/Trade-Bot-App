import tempfile
from pathlib import Path

from app.trading.submission_ledger import SubmissionLedger
from app.trading.submission_recovery import SubmissionRecovery


class FakeBroker:
    def __init__(self):
        self.lookups = 0
        self.submissions = 0

    def get_order_by_client_id(self, client_order_id):
        self.lookups += 1
        return {
            "id": "BROKER-RECOVERED-1",
            "client_order_id": client_order_id,
            "status": "accepted",
        }

    def submit_order(self, payload):
        self.submissions += 1
        raise AssertionError("Recovery must never submit an order.")


print("=== TRADING APP v2.0 / AMBIGUOUS SUBMISSION RECOVERY ===")

with tempfile.TemporaryDirectory() as directory:
    ledger = SubmissionLedger(Path(directory) / "ledger.json")
    ledger.reserve("BOT-1-ORDER-1", "SPY|buy|0.02|500")

    broker = FakeBroker()
    result = SubmissionRecovery(broker, ledger).resolve("BOT-1-ORDER-1")

    assert result["recovered"] is True
    assert result["broker_order_id"] == "BROKER-RECOVERED-1"
    assert broker.lookups == 1
    assert broker.submissions == 0

    print("Persisted reservation found: PASS")
    print("Broker queried by client_order_id: PASS")
    print("Existing broker order recovered: PASS")
    print("Blind resubmission prevented: PASS")

print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
