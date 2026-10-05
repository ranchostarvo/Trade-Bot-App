import json
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from .risk import RiskRejected


@dataclass(frozen=True)
class CapitalConfig:
    max_total_allocated: Decimal
    reserve_cash: Decimal = Decimal("0")


class PortfolioCapitalCoordinator:
    """Fail-closed portfolio-wide persistent capital reservations."""

    def __init__(self, config, path=None):
        self.config = config
        self.path = Path(path) if path is not None else None
        self._reservations = self._read() if self.path is not None else {}

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text())
            if not isinstance(raw, dict):
                raise ValueError("capital reservation root must be an object")
            parsed = {}
            for key, value in raw.items():
                amount = Decimal(str(value))
                if amount <= 0:
                    raise ValueError("capital reservations must be positive")
                parsed[str(key)] = amount
            return parsed
        except Exception as exc:
            raise RiskRejected(
                f"Unable to read capital reservations: {exc}"
            ) from exc

    def _write(self):
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(
            {key: str(value) for key, value in self._reservations.items()},
            sort_keys=True,
            indent=2,
        ))
        os.replace(temporary, self.path)

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
        self._write()
        return after

    def release(self, reservation_id):
        value = self._reservations.pop(str(reservation_id), Decimal("0"))
        self._write()
        return value
