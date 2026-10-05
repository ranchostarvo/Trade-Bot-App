from dataclasses import dataclass
from decimal import Decimal

from .risk import RiskRejected


@dataclass(frozen=True)
class PositionAllocation:
    allocation_id: str
    symbol: str
    quantity: Decimal
    invested_notional: Decimal


class PositionAllocationBook:
    """Maps sell quantity deterministically to persistent invested allocations."""

    def __init__(self, exposure_ledger):
        self.exposure = exposure_ledger
        self._positions = {}

    def record_buy(self, allocation_id, symbol, quantity, invested_notional):
        key = str(allocation_id or "").strip()
        symbol = str(symbol or "").strip().upper()
        quantity = Decimal(str(quantity))
        notional = Decimal(str(invested_notional))
        if not key or not symbol or quantity <= 0 or notional <= 0:
            raise RiskRejected("Valid buy allocation data is required.")
        if key in self._positions:
            raise RiskRejected("Duplicate position allocation.")
        self.exposure.allocate(key, notional)
        self._positions[key] = PositionAllocation(key, symbol, quantity, notional)
        return self._positions[key]

    def release_sell(self, symbol, quantity):
        symbol = str(symbol or "").strip().upper()
        remaining = Decimal(str(quantity))
        if not symbol or remaining <= 0:
            raise RiskRejected("Valid sell symbol and quantity are required.")

        matches = [p for p in self._positions.values() if p.symbol == symbol]
        available = sum((p.quantity for p in matches), Decimal("0"))
        if remaining > available:
            raise RiskRejected("Sell quantity exceeds mapped invested position.")

        released = Decimal("0")
        # FIFO allocation provides deterministic, reproducible accounting.
        for position in list(matches):
            if remaining <= 0:
                break
            take = min(position.quantity, remaining)
            ratio = take / position.quantity
            notional = position.invested_notional * ratio
            self.exposure.release(position.allocation_id, notional)
            released += notional
            remaining -= take
            left_qty = position.quantity - take
            if left_qty == 0:
                self._positions.pop(position.allocation_id)
            else:
                left_notional = position.invested_notional - notional
                self._positions[position.allocation_id] = PositionAllocation(
                    position.allocation_id, position.symbol, left_qty, left_notional
                )
        return released
