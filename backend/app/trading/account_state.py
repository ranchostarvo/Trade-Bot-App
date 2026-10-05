from decimal import Decimal, InvalidOperation

from .risk import AccountRiskState, RiskRejected


class AlpacaAccountStateProvider:
    def __init__(self, alpaca_client):
        self.alpaca = alpaca_client

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
            start_equity = Decimal(
                str(account["last_equity"])
            )
            current_equity = Decimal(
                str(account["equity"])
            )
        except (KeyError, InvalidOperation, TypeError) as exc:
            raise RiskRejected(
                "Invalid Alpaca equity data."
            ) from exc

        if start_equity <= 0:
            raise RiskRejected(
                "Alpaca last_equity must be greater than zero."
            )

        if current_equity < 0:
            raise RiskRejected(
                "Alpaca equity cannot be negative."
            )

        return AccountRiskState(
            start_of_day_equity=start_equity,
            current_equity=current_equity,
        )
