from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from app.trading.runtime_factory import RuntimePaths, build_paper_runtime


class Config:
    paper = True


class Broker:
    config = Config()
    def get_account(self):
        return {
            "equity": "100000",
            "last_equity": "100000",
            "cash": "100000",
            "trading_blocked": False,
            "account_blocked": False,
        }
    def get_calendar(self, start, end):
        return []


with TemporaryDirectory() as directory:
    runtime = build_paper_runtime(
        directory,
        broker=Broker(),
        allow_test_broker=True,
    )
    paths = RuntimePaths(Path(directory))
    execution = runtime.execution_engine

    assert execution.capital_coordinator is not None
    assert execution.available_cash_provider is not None
    assert execution.available_cash_provider() == Decimal("100000")
    assert execution.capital_coordinator.path == paths.capital_reservations
    assert execution.capital_coordinator.config.max_total_allocated == Decimal("50000")
    assert execution.capital_coordinator.config.reserve_cash == Decimal("5000")

print("=== TRADING APP v2.0 / CAPITAL RUNTIME WIRING ===")
print("Persistent coordinator wired: PASS")
print("Validated account cash provider wired: PASS")
print("Default portfolio ceiling $50,000: PASS")
print("Default reserve cash $5,000: PASS")
print("Broker writes: NONE")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
