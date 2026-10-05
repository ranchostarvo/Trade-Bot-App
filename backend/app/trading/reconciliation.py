from dataclasses import dataclass
from decimal import Decimal

from app.brokers.alpaca import AlpacaClient, AlpacaError
from .position import Position, PositionBook


@dataclass(frozen=True)
class AccountSnapshot:
    cash: Decimal
    equity: Decimal
    buying_power: Decimal
    trading_blocked: bool
    account_blocked: bool


class AlpacaReconciler:
    """Read-only broker reconciliation. No order submission capability."""

    def __init__(self, client: AlpacaClient):
        self.client = client

    def account_snapshot(self) -> AccountSnapshot:
        data = self.client.get_account()
        try:
            return AccountSnapshot(
                cash=Decimal(str(data["cash"])),
                equity=Decimal(str(data["equity"])),
                buying_power=Decimal(str(data["buying_power"])),
                trading_blocked=bool(data.get("trading_blocked", False)),
                account_blocked=bool(data.get("account_blocked", False)),
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise AlpacaError("Account response is missing required values.") from exc

    def position_book(self) -> PositionBook:
        data = self.client.get_positions()
        if not isinstance(data, list):
            raise AlpacaError("Positions response must be a list.")
        positions = []
        try:
            for item in data:
                positions.append(
                    Position(
                        symbol=str(item["symbol"]).upper(),
                        quantity=Decimal(str(item["qty"])),
                    )
                )
        except (KeyError, ValueError, TypeError) as exc:
            raise AlpacaError("Position response is malformed.") from exc
        return PositionBook(positions)

    def reconcile(self):
        account = self.account_snapshot()
        positions = self.position_book()
        return account, positions


    def order_status(self, order_id: str) -> str:
        data = self.client.get_order(order_id)
        if not isinstance(data, dict):
            raise AlpacaError("Order response must be an object.")
        status = str(data.get("status", "")).strip().lower()
        if not status:
            raise AlpacaError("Order response is missing status.")
        return status
