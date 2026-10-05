from dataclasses import dataclass
from decimal import Decimal

from app.trading.broker_risk import BrokerRiskStateProvider
from app.trading.risk import RiskRejected


@dataclass
class Account:
    equity: Decimal
    account_blocked: bool = False
    trading_blocked: bool = False


class Reconciler:
    def __init__(self, equity):
        self.equity = Decimal(equity)

    def account_snapshot(self):
        return Account(self.equity)


class Store:
    def __init__(self):
        self.data = {}

    def set_state(self, key, value):
        self.data[key] = value

    def get_state(self, key, default=None):
        return self.data.get(key, default)


def test_broker_equity_baseline_persists_and_drives_loss_pct():
    store = Store()
    reconciler = Reconciler("100000")
    provider = BrokerRiskStateProvider(reconciler, store)
    provider.initialize_day()

    reconciler.equity = Decimal("97500")
    state = provider.current()

    assert str(state.start_of_day_equity) == "100000"
    assert str(state.current_equity) == "97500"
    assert state.daily_loss_pct == Decimal("2.500")


def test_missing_daily_baseline_fails_closed():
    provider = BrokerRiskStateProvider(Reconciler("100000"), Store())
    try:
        provider.current()
    except RiskRejected as exc:
        assert "not initialized" in str(exc)
        return
    raise AssertionError("Risk state proceeded without daily baseline.")


def test_invalid_equity_baseline_fails_closed():
    store = Store()
    store.set_state("risk_start_of_day_equity", {"equity": "bad"})
    provider = BrokerRiskStateProvider(Reconciler("100000"), store)
    try:
        provider.current()
    except RiskRejected:
        return
    raise AssertionError("Invalid baseline was accepted.")
