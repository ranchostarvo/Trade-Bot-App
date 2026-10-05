from decimal import Decimal, InvalidOperation

from .risk import AccountRiskState, RiskRejected


class AlpacaAccountStateProvider:
    def __init__(
        self,
        alpaca_client,
        equity_baseline_store=None,
    ):
        self.alpaca = alpaca_client
        self.equity_baseline_store = (
            equity_baseline_store
        )

    def get_risk_state(self):
        account = self.alpaca.get_account()

        if account.get("trading_blocked"):
            raise RiskRejected(
                "Alpaca reports that trading is blocked."
            )

        if account.get("account_blocked"):
            raise RiskRejected(
                "Alpaca reports that the account is blocked."
            )

        try:
            current_equity = Decimal(
                str(account["equity"])
            )
            alpaca_last_equity = Decimal(
                str(account["last_equity"])
            )
        except (
            KeyError,
            InvalidOperation,
            TypeError,
        ) as exc:
            raise RiskRejected(
                "Invalid Alpaca equity data."
            ) from exc

        if current_equity <= 0:
            raise RiskRejected(
                "Alpaca equity must be greater than zero."
            )

        if alpaca_last_equity <= 0:
            raise RiskRejected(
                "Alpaca last_equity must be greater than zero."
            )

        if self.equity_baseline_store is not None:
            start_equity = (
                self.equity_baseline_store.get_or_create(
                    current_equity
                )
            )
        else:
            # Compatibility fallback for read-only tests.
            start_equity = alpaca_last_equity

        return AccountRiskState(
            start_of_day_equity=start_equity,
            current_equity=current_equity,
        )
