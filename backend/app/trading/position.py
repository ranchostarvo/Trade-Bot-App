from dataclasses import dataclass
from decimal import Decimal

from .risk import OrderRequest, RiskRejected


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: Decimal


class PositionBook:
    """Read-only position view used for pre-trade validation."""

    def __init__(self, positions=()):
        self._positions = {
            p.symbol.strip().upper(): p.quantity for p in positions
        }

    def quantity(self, symbol: str) -> Decimal:
        return self._positions.get(symbol.strip().upper(), Decimal("0"))


@dataclass(frozen=True)
class PositionPolicy:
    allow_short_selling: bool = False


class PositionValidator:
    def __init__(self, book: PositionBook, policy=None):
        self.book = book
        self.policy = policy or PositionPolicy()

    def validate(self, order: OrderRequest) -> None:
        if order.side.lower() != "sell":
            return
        if self.policy.allow_short_selling:
            return

        owned = self.book.quantity(order.symbol)
        if order.quantity > owned:
            raise RiskRejected(
                f"Sell quantity {order.quantity} exceeds owned quantity "
                f"{owned} for {order.symbol}; short selling is disabled."
            )
