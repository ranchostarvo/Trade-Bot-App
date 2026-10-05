from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


class PositionMismatch(RuntimeError):
    pass


@dataclass(frozen=True)
class PositionState:
    symbol: str
    quantity: Decimal
    average_entry_price: Decimal
    market_value: Decimal


class PositionReconciler:
    def __init__(self, broker):
        self.broker = broker

    def get_position(self, symbol: str) -> PositionState:
        symbol = str(symbol or "").strip().upper()
        if not symbol:
            raise ValueError("Symbol is required.")

        raw = self.broker.get_position(symbol)

        try:
            quantity = Decimal(str(raw["qty"]))
            average_entry_price = Decimal(str(raw["avg_entry_price"]))
            market_value = Decimal(str(raw["market_value"]))
        except (KeyError, InvalidOperation, TypeError) as exc:
            raise ValueError("Broker returned invalid position data.") from exc

        return PositionState(
            symbol=str(raw.get("symbol") or symbol).upper(),
            quantity=quantity,
            average_entry_price=average_entry_price,
            market_value=market_value,
        )

    def reconcile_minimum_fill(self, symbol: str, expected_min_qty: Decimal):
        position = self.get_position(symbol)
        expected_min_qty = Decimal(str(expected_min_qty))

        if position.quantity < expected_min_qty:
            raise PositionMismatch(
                f"{position.symbol} broker quantity {position.quantity} "
                f"is below expected minimum {expected_min_qty}."
            )

        return position

    def reconcile_expected(self, symbol: str, expected_qty: Decimal):
        position = self.get_position(symbol)
        expected_qty = Decimal(str(expected_qty))

        if position.quantity != expected_qty:
            raise PositionMismatch(
                f"{position.symbol} broker quantity {position.quantity} "
                f"does not match expected quantity {expected_qty}."
            )

        return position
