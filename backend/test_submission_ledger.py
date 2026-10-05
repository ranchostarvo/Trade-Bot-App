import tempfile
from pathlib import Path

from app.trading.submission_ledger import DuplicateOrder, SubmissionLedger


print("=== TRADING APP v2.0 / DUPLICATE ORDER PROTECTION ===")

with tempfile.TemporaryDirectory() as directory:
    ledger = SubmissionLedger(Path(directory) / "submissions.json")
    ledger.reserve("BOT-1-ORDER-1", "SPY|buy|0.02")
    assert ledger.get("BOT-1-ORDER-1")["fingerprint"] == "SPY|buy|0.02"
    print("First reservation persisted: PASS")

    try:
        ledger.reserve("BOT-1-ORDER-1", "SPY|buy|0.02")
        raise AssertionError("Duplicate order was not blocked.")
    except DuplicateOrder:
        print("Duplicate reservation blocked: PASS")

    restarted = SubmissionLedger(Path(directory) / "submissions.json")
    try:
        restarted.reserve("BOT-1-ORDER-1", "SPY|buy|0.02")
        raise AssertionError("Restart duplicate was not blocked.")
    except DuplicateOrder:
        print("Duplicate blocked after restart: PASS")

print("Broker interaction: NO")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
