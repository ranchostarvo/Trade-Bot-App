import json
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from .risk import RiskRejected


@dataclass(frozen=True)
class PositionAllocation:
    allocation_id: str
    symbol: str
    quantity: Decimal
    invested_notional: Decimal


class PositionAllocationBook:
    """Maps sell quantity deterministically to persistent invested allocations."""

    def __init__(self, exposure_ledger, path=None):
        self.exposure = exposure_ledger
        self.path = Path(path) if path is not None else None
        self._positions = self._read()

    def _read(self):
        if self.path is None or not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text())
            if not isinstance(raw, dict):
                raise ValueError("position allocation root must be an object")
            result = {}
            for key, value in raw.items():
                result[key] = PositionAllocation(
                    key,
                    str(value["symbol"]).upper(),
                    Decimal(str(value["quantity"])),
                    Decimal(str(value["invested_notional"])),
                )
                if result[key].quantity <= 0 or result[key].invested_notional <= 0:
                    raise ValueError("position allocations must be positive")
            return result
        except Exception as exc:
            raise RiskRejected(f"Unable to read position allocations: {exc}") from exc

    def _write(self):
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps({
            key: {
                "symbol": value.symbol,
                "quantity": str(value.quantity),
                "invested_notional": str(value.invested_notional),
            }
            for key, value in self._positions.items()
        }, sort_keys=True, indent=2))
        os.replace(temporary, self.path)

    def get(self, allocation_id):
        return self._positions.get(str(allocation_id))

    def total_quantity(self, symbol):
        symbol = str(symbol or "").strip().upper()
        return sum(
            (p.quantity for p in self._positions.values() if p.symbol == symbol),
            Decimal("0"),
        )

    def record_allocated_buy(self, allocation_id, symbol, quantity, invested_notional):
        """Persist mapping when exposure was already allocated by capital transition."""
        key = str(allocation_id or "").strip()
        symbol = str(symbol or "").strip().upper()
        quantity = Decimal(str(quantity))
        notional = Decimal(str(invested_notional))
        if not key or not symbol or quantity <= 0 or notional <= 0:
            raise RiskRejected("Valid buy allocation data is required.")
        existing = self._positions.get(key)
        if existing is not None:
            if existing.symbol == symbol and existing.quantity == quantity and existing.invested_notional == notional:
                return existing
            raise RiskRejected("Conflicting position allocation.")
        self._positions[key] = PositionAllocation(key, symbol, quantity, notional)
        self._write()
        return self._positions[key]

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
        self._write()
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
            self._write()
        return released
