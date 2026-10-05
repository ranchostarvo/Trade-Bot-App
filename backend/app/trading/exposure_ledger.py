import json
import os
from decimal import Decimal
from pathlib import Path

from .risk import RiskRejected


class PortfolioExposureLedger:
    """Persistent invested-capital accounting, separate from open-order cash."""

    def __init__(self, path, max_invested):
        self.path = Path(path)
        self.max_invested = Decimal(str(max_invested))
        if self.max_invested <= 0:
            raise ValueError("max_invested must be positive.")
        self._allocations = self._read()

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text())
            if not isinstance(raw, dict):
                raise ValueError("exposure ledger root must be an object")
            values = {str(k): Decimal(str(v)) for k, v in raw.items()}
            if any(v < 0 for v in values.values()):
                raise ValueError("negative invested allocation")
            if sum(values.values(), Decimal("0")) > self.max_invested:
                raise ValueError("persisted exposure exceeds portfolio ceiling")
            return values
        except Exception as exc:
            raise RiskRejected(f"Unable to read portfolio exposure ledger: {exc}") from exc

    def _write(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(
            {k: str(v) for k, v in self._allocations.items()},
            sort_keys=True,
            indent=2,
        ))
        os.replace(temporary, self.path)

    @property
    def total_invested(self):
        return sum(self._allocations.values(), Decimal("0"))

    @property
    def remaining_capacity(self):
        return self.max_invested - self.total_invested

    def get(self, allocation_id):
        return self._allocations.get(str(allocation_id), Decimal("0"))

    def allocate(self, allocation_id, amount):
        allocation_id = str(allocation_id or "").strip()
        amount = Decimal(str(amount))
        if not allocation_id or amount <= 0:
            raise RiskRejected("Allocation ID and positive amount are required.")
        if allocation_id in self._allocations:
            raise RiskRejected("Duplicate invested allocation.")
        if self.total_invested + amount > self.max_invested:
            raise RiskRejected("Portfolio invested-capital ceiling exceeded.")
        self._allocations[allocation_id] = amount
        self._write()
        return amount

    def release(self, allocation_id, amount=None):
        allocation_id = str(allocation_id or "").strip()
        current = self._allocations.get(allocation_id, Decimal("0"))
        if current <= 0:
            return Decimal("0")
        if amount is None:
            released = current
        else:
            released = Decimal(str(amount))
            if released <= 0 or released > current:
                raise RiskRejected("Invalid invested-capital release.")
        remaining = current - released
        if remaining == 0:
            self._allocations.pop(allocation_id, None)
        else:
            self._allocations[allocation_id] = remaining
        self._write()
        return released
