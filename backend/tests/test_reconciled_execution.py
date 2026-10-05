from dataclasses import dataclass
from decimal import Decimal

from app.trading.execution import ExecutionEngine
from app.trading.position import Position, PositionBook
from app.trading.risk import OrderRequest, RiskRejected


@dataclass
class Account:
    account_blocked: bool = False
    trading_blocked: bool = False


class Reconciler:
    def __init__(self, quantity, blocked=False):
        self.quantity = Decimal(quantity)
        self.blocked = blocked

    def reconcile(self):
        return (
            Account(
                account_blocked=self.blocked,
                trading_blocked=self.blocked,
            ),
            PositionBook([Position("SPY", self.quantity)]),
        )


def sell(quantity):
    return OrderRequest(
        symbol="SPY",
        side="sell",
        quantity=Decimal(quantity),
        estimated_price=Decimal("100"),
    )


def test_sell_requires_broker_reconciliation():
    try:
        ExecutionEngine().execute(sell("1"))
    except RuntimeError as exc:
        assert "reconciliation is required" in str(exc)
        return
    raise AssertionError("Sell proceeded without broker reconciliation.")


def test_reconciled_owned_sell_remains_dry_run():
    result = ExecutionEngine(
        reconciler=Reconciler("5")
    ).execute(sell("2"))
    assert result["status"] == "DRY_RUN"
    assert result["submitted"] is False


def test_reconciled_oversell_is_rejected():
    try:
        ExecutionEngine(
            reconciler=Reconciler("1")
        ).execute(sell("2"))
    except RiskRejected:
        return
    raise AssertionError("Oversell passed broker position validation.")


def test_blocked_broker_account_rejects_sell():
    try:
        ExecutionEngine(
            reconciler=Reconciler("5", blocked=True)
        ).execute(sell("1"))
    except RuntimeError as exc:
        assert "blocked" in str(exc)
        return
    raise AssertionError("Blocked account was allowed to sell.")
