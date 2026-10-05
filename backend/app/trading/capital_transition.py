from decimal import Decimal

from .risk import RiskRejected


class CapitalTransition:
    """Move capital between open-order reservations and invested exposure."""

    def __init__(self, reservations, exposure):
        self.reservations = reservations
        self.exposure = exposure

    def buy_fill(self, reservation_id, allocation_id, filled_notional, terminal=False):
        filled = Decimal(str(filled_notional))
        if filled <= 0:
            raise RiskRejected("Filled notional must be positive.")

        reserved = self.reservations.get(reservation_id)
        if reserved <= 0:
            raise RiskRejected("Expected open-order capital reservation is missing.")
        if filled > reserved:
            raise RiskRejected("Filled notional exceeds reserved capital.")

        # Exposure is persisted before reservation is reduced. If a crash occurs
        # between writes, capital is conservatively double-counted, never freed.
        self.exposure.allocate(allocation_id, filled)

        remaining = reserved - filled
        if terminal:
            self.reservations.release(reservation_id)
        elif remaining == 0:
            self.reservations.release(reservation_id)
        else:
            self.reservations.reduce_to(reservation_id, remaining)
        return {
            "invested": filled,
            "reserved_remaining": Decimal("0") if terminal else remaining,
        }

    def sell_fill(self, allocation_id, filled_notional):
        released = Decimal(str(filled_notional))
        if released <= 0:
            raise RiskRejected("Sell fill notional must be positive.")
        current = self.exposure.get(allocation_id)
        if current <= 0:
            raise RiskRejected("Expected invested allocation is missing.")
        if released > current:
            raise RiskRejected("Sell release exceeds invested allocation.")
        self.exposure.release(allocation_id, released)
        return released
