from dataclasses import dataclass
from decimal import Decimal

from .risk import RiskRejected


@dataclass(frozen=True)
class CapitalConfig:
    max_total_allocated: Decimal
    reserve_cash: Decimal = Decimal("0")


class PortfolioCapitalCoordinator:
    """Fail-closed portfolio-wide capital reservation across many bots."""

    def __init__(self, config):
        self.config = config
        self._reservations = {}

    @property
    def allocated(self):
        return sum(self._reservations.values(), Decimal("0"))

    def reserve(self, reservation_id, notional, available_cash):
        reservation_id = str(reservation_id or "").strip()
        if not reservation_id:
            raise RiskRejected("Capital reservation ID is required.")

        amount = Decimal(str(notional))
        cash = Decimal(str(available_cash))
        if amount <= 0:
            raise RiskRejected("Capital reservation must be positive.")
        if cash < 0:
            raise RiskRejected("Available cash cannot be negative.")
        if reservation_id in self._reservations:
            raise RiskRejected("Duplicate capital reservation.")

        after = self.allocated + amount
        if after > self.config.max_total_allocated:
            raise RiskRejected("Portfolio allocation ceiling exceeded.")
        if after > cash - self.config.reserve_cash:
            raise RiskRejected("Insufficient unreserved portfolio cash.")

        self._reservations[reservation_id] = amount
        return after

    def release(self, reservation_id):
        return self._reservations.pop(str(reservation_id), Decimal("0"))
