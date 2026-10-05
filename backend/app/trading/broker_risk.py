from dataclasses import dataclass
from decimal import Decimal

from .risk import AccountRiskState, RiskRejected


@dataclass(frozen=True)
class DailyEquityBaseline:
    equity: Decimal


class BrokerRiskStateProvider:
    """Builds risk state from reconciled broker equity plus a stored baseline."""

    def __init__(self, reconciler, store, state_key="risk_start_of_day_equity"):
        self.reconciler = reconciler
        self.store = store
        self.state_key = state_key

    def initialize_day(self) -> DailyEquityBaseline:
        account = self.reconciler.account_snapshot()
        if account.account_blocked or account.trading_blocked:
            raise RiskRejected("Broker account is blocked from trading.")
        if account.equity <= 0:
            raise RiskRejected("Broker equity must be greater than zero.")
        baseline = DailyEquityBaseline(account.equity)
        self.store.set_state(self.state_key, {"equity": str(baseline.equity)})
        return baseline

    def current(self) -> AccountRiskState:
        saved = self.store.get_state(self.state_key)
        if not saved or "equity" not in saved:
            raise RiskRejected(
                "Start-of-day broker equity baseline is not initialized."
            )

        account = self.reconciler.account_snapshot()
        if account.account_blocked or account.trading_blocked:
            raise RiskRejected("Broker account is blocked from trading.")

        try:
            start = Decimal(str(saved["equity"]))
        except (ValueError, TypeError) as exc:
            raise RiskRejected("Stored equity baseline is invalid.") from exc

        return AccountRiskState(
            start_of_day_equity=start,
            current_equity=account.equity,
        )
