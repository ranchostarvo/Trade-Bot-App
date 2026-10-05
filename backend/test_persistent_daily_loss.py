import tempfile
from decimal import Decimal
from pathlib import Path

from app.trading.account_state import (
    AlpacaAccountStateProvider,
)
from app.trading.equity_baseline import (
    EquityBaselineStore,
)
from app.trading.risk import RiskEngine, RiskRejected


class FakeAlpaca:
    def __init__(self, equity):
        self.equity = equity

    def get_account(self):
        return {
            "equity": str(self.equity),
            "last_equity": "100000",
            "trading_blocked": False,
            "account_blocked": False,
        }


print(
    "=== TRADING APP v2.0 / "
    "PERSISTENT DAILY LOSS ==="
)

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "equity.json"

    baseline_store = EquityBaselineStore(path)
    risk = RiskEngine()

    first_provider = AlpacaAccountStateProvider(
        FakeAlpaca(Decimal("100000")),
        equity_baseline_store=baseline_store,
    )

    first_state = first_provider.get_risk_state()

    assert (
        first_state.start_of_day_equity
        == Decimal("100000")
    )

    print("Baseline established: PASS")

    # Simulate application restart after a 2% loss.
    restarted_provider = AlpacaAccountStateProvider(
        FakeAlpaca(Decimal("98000")),
        equity_baseline_store=EquityBaselineStore(path),
    )

    restarted_state = (
        restarted_provider.get_risk_state()
    )

    assert (
        restarted_state.start_of_day_equity
        == Decimal("100000")
    )

    allowed_loss = risk.validate_daily_loss(
        restarted_state
    )

    assert allowed_loss == Decimal("2.00")

    print(
        "2% loss survives restart and remains allowed: PASS"
    )

    # Simulate another restart at the 2.5% limit.
    limit_provider = AlpacaAccountStateProvider(
        FakeAlpaca(Decimal("97500")),
        equity_baseline_store=EquityBaselineStore(path),
    )

    limit_state = limit_provider.get_risk_state()

    try:
        risk.validate_daily_loss(limit_state)
        raise AssertionError(
            "2.5% persistent loss was not blocked."
        )
    except RiskRejected:
        print(
            "2.5% persistent daily loss blocked: PASS"
        )

print("No broker interaction: PASS")
print("RESULT: PASS")
