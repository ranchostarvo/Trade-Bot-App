from dataclasses import dataclass
from decimal import Decimal
from threading import RLock


class AllocationRejected(RuntimeError):
    """Raised when capital cannot be safely reserved."""


@dataclass(frozen=True)
class AllocationSnapshot:
    account_cash: Decimal
    reserved_cash: Decimal
    available_cash: Decimal


class CapitalAllocator:
    def __init__(self, account_cash: Decimal):
        if account_cash < 0:
            raise ValueError("Account cash cannot be negative.")
        self._account_cash = account_cash
        self._reservations: dict[str, Decimal] = {}
        self._lock = RLock()

    @property
    def reserved_cash(self) -> Decimal:
        return sum(self._reservations.values(), Decimal("0"))

    @property
    def available_cash(self) -> Decimal:
        return self._account_cash - self.reserved_cash

    def snapshot(self) -> AllocationSnapshot:
        return AllocationSnapshot(
            account_cash=self._account_cash,
            reserved_cash=self.reserved_cash,
            available_cash=self.available_cash,
        )

    def reserve(self, bot_id: str, amount: Decimal) -> AllocationSnapshot:
        with self._lock:
            return self._reserve_locked(bot_id, amount)

    def _reserve_locked(self, bot_id: str, amount: Decimal) -> AllocationSnapshot:
        bot_id = bot_id.strip()
        if not bot_id:
            raise AllocationRejected("bot_id is required.")
        if amount <= 0:
            raise AllocationRejected("Reservation amount must be greater than zero.")
        if bot_id in self._reservations:
            raise AllocationRejected(f"Bot {bot_id} already has a reservation.")
        if amount > self.available_cash:
            raise AllocationRejected(
                f"Insufficient unreserved cash: requested ${amount}, "
                f"available ${self.available_cash}."
            )
        self._reservations[bot_id] = amount
        return self.snapshot()

    def release(self, bot_id: str) -> AllocationSnapshot:
        if bot_id not in self._reservations:
            raise AllocationRejected(f"No reservation exists for bot {bot_id}.")
        del self._reservations[bot_id]
        return self.snapshot()

    def resize_account_cash(self, account_cash: Decimal) -> AllocationSnapshot:
        if account_cash < 0:
            raise ValueError("Account cash cannot be negative.")
        if account_cash < self.reserved_cash:
            raise AllocationRejected(
                "Account cash cannot be reduced below currently reserved cash."
            )
        self._account_cash = account_cash
        return self.snapshot()
