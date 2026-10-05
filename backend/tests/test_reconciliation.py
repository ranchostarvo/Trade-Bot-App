from app.trading.reconciliation import AlpacaReconciler


class FakeClient:
    def get_account(self):
        return {
            "cash": "100000",
            "equity": "100000",
            "buying_power": "400000",
            "trading_blocked": False,
            "account_blocked": False,
        }

    def get_positions(self):
        return [
            {"symbol": "SPY", "qty": "3.5"},
            {"symbol": "QQQ", "qty": "2"},
        ]


def test_reconciliation_builds_account_and_position_views():
    account, positions = AlpacaReconciler(FakeClient()).reconcile()
    assert str(account.cash) == "100000"
    assert str(account.equity) == "100000"
    assert str(account.buying_power) == "400000"
    assert str(positions.quantity("SPY")) == "3.5"
    assert str(positions.quantity("qqq")) == "2"


def test_reconciler_exposes_no_order_submission():
    reconciler = AlpacaReconciler(FakeClient())
    assert not hasattr(reconciler, "submit_order")
