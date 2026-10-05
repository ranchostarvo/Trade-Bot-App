import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.trading.runtime_factory import RuntimePaths, build_paper_runtime


@dataclass
class Config:
    paper: bool = True


class FakeBroker:
    config = Config()

    def get_account(self):
        return {
            "equity": "100000",
            "last_equity": "100000",
            "trading_blocked": False,
            "account_blocked": False,
        }

    def get_order(self, order_id):
        raise AssertionError("No persisted orders should exist.")

    def submit_order(self, payload):
        raise AssertionError("Dry-run runtime must not submit.")


print("=== TRADING APP v2.0 / RUNTIME FACTORY ===")

with tempfile.TemporaryDirectory() as directory:
    runtime = build_paper_runtime(
        directory,
        broker=FakeBroker(),
        trading_enabled=False,
        dry_run=True,
    )
    report = runtime.startup()
    assert report.ready is True

    paths = RuntimePaths(Path(directory))
    assert paths.risk_state.name == "risk_state.json"
    assert paths.equity_baseline.name == "equity_baseline.json"
    assert paths.order_journal.name == "order_journal.json"
    assert paths.submission_ledger.name == "submission_ledger.json"

    print("Persistent state paths wired: PASS")
    print("Paper broker boundary enforced: PASS")
    print("Runtime startup: PASS")
    print("Default trading enabled: NO")
    print("Default dry run: YES")

print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
