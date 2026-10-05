import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .position_reconciler import PositionMismatch


class PositionSnapshotStore:
    def __init__(self, path):
        self.path = Path(path)

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise PositionMismatch(
                f"Unable to read position snapshot: {exc}"
            ) from exc
        if not isinstance(data, dict):
            raise PositionMismatch("Invalid position snapshot.")
        return data

    def _write(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            with temp.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, sort_keys=True)
                handle.flush()
            temp.replace(self.path)
        except OSError as exc:
            raise PositionMismatch(
                f"Unable to save position snapshot: {exc}"
            ) from exc

    def set(self, symbol, quantity):
        symbol = str(symbol or "").strip().upper()
        if not symbol:
            raise PositionMismatch("Symbol is required.")
        try:
            quantity = Decimal(str(quantity))
        except (InvalidOperation, TypeError) as exc:
            raise PositionMismatch("Invalid expected position quantity.") from exc

        data = self._read()
        data[symbol] = str(quantity)
        self._write(data)
        return quantity

    def get(self, symbol):
        symbol = str(symbol or "").strip().upper()
        data = self._read()
        if symbol not in data:
            return None
        try:
            return Decimal(str(data[symbol]))
        except (InvalidOperation, TypeError) as exc:
            raise PositionMismatch(
                f"Invalid persisted position for {symbol}."
            ) from exc
