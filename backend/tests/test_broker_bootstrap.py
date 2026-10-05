from decimal import Decimal

import pytest

from app.bootstrap import BrokerBootstrap, BootstrapBlocked
from app.storage import SQLiteStore
from app.trading.reconciliation import AccountSnapshot


class FakeReconcilerClient:
    def __init__(self, blocked=False, cash="25000", equity="100000"):
        self.blocked = blocked
        self.cash = cash
        self.equity = equity

    def get_account(self):
        return {
            "cash": self.cash,
            "equity": self.equity,
            "buying_power": "200000",
            "trading_blocked": self.blocked,
            "account_blocked": False,
        }

    def get_positions(self):
        return []

    def get_order(self, order_id):
        raise AssertionError("No order lookup expected during bootstrap.")


def test_bootstrap_uses_broker_cash_and_equity(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    result = BrokerBootstrap.build(
        store=store,
        client=FakeReconcilerClient(cash="25000", equity="100000"),
    )

    assert result.runtime.resources.account_cash == Decimal("25000")
    assert result.runtime.resources.account_equity == Decimal("100000")
    assert result.runtime.store is store
    assert result.runtime.execution.reconciler is result.reconciler


def test_bootstrap_rejects_blocked_broker_account(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    with pytest.raises(BootstrapBlocked, match="blocked"):
        BrokerBootstrap.build(store=store, client=FakeReconcilerClient(blocked=True))


@pytest.mark.parametrize(
    "cash,equity",
    [("0", "100000"), ("25000", "0"), ("-1", "100000")],
)
def test_bootstrap_rejects_nonpositive_account_values(tmp_path, cash, equity):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    with pytest.raises(BootstrapBlocked, match="positive"):
        BrokerBootstrap.build(
            store=store,
            client=FakeReconcilerClient(cash=cash, equity=equity),
        )
