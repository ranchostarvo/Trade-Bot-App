from dataclasses import dataclass
from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.resources import DurableResourceCoordinator, DurableResourceRejected


@dataclass
class Account:
    cash: Decimal
    equity: Decimal
    account_blocked: bool = False
    trading_blocked: bool = False


class Reconciler:
    def __init__(self, cash="50000", equity="100000", blocked=False):
        self.account = Account(
            Decimal(cash), Decimal(equity), blocked, blocked
        )

    def account_snapshot(self):
        return self.account


def test_resource_coordinator_uses_reconciled_broker_values(tmp_path):
    coordinator = DurableResourceCoordinator.from_reconciler(
        SQLiteStore(str(tmp_path / "trading.db")),
        Reconciler(cash="12345", equity="67890"),
    )
    assert coordinator.account_cash == Decimal("12345")
    assert coordinator.account_equity == Decimal("67890")


def test_blocked_broker_account_fails_closed(tmp_path):
    try:
        DurableResourceCoordinator.from_reconciler(
            SQLiteStore(str(tmp_path / "trading.db")),
            Reconciler(blocked=True),
        )
    except DurableResourceRejected as exc:
        assert "blocked" in str(exc)
        return
    raise AssertionError("Blocked broker account initialized resources.")


def test_invalid_broker_equity_fails_closed(tmp_path):
    try:
        DurableResourceCoordinator.from_reconciler(
            SQLiteStore(str(tmp_path / "trading.db")),
            Reconciler(equity="0"),
        )
    except DurableResourceRejected:
        return
    raise AssertionError("Invalid broker equity initialized resources.")
