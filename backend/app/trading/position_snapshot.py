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

    def seed_accounted_fill(self, order_id, cumulative_filled_qty):
        """Seed legacy recovery progress without changing the position."""
        order_id = str(order_id or "").strip()
        if not order_id:
            raise PositionMismatch("Order ID is required.")
        try:
            cumulative = Decimal(str(cumulative_filled_qty))
        except (InvalidOperation, TypeError) as exc:
            raise PositionMismatch("Invalid cumulative fill quantity.") from exc
        if cumulative < 0:
            raise PositionMismatch("Cumulative fill quantity cannot be negative.")

        data = self._read()
        if "_positions" not in data:
            data = {
                "_positions": {
                    key: value for key, value in data.items()
                    if not key.startswith("_")
                },
                "_accounted_fills": {},
            }
        accounted = data.setdefault("_accounted_fills", {})
        existing = Decimal(str(accounted.get(order_id, "0")))
        if existing > cumulative:
            raise PositionMismatch("Accounted fill exceeds legacy recovery state.")
        accounted[order_id] = str(cumulative)
        self._write(data)
        return cumulative

    def apply_fill_once(self, order_id, symbol, side, cumulative_filled_qty):
        """Atomically persist position and per-order cumulative fill progress."""
        order_id = str(order_id or "").strip()
        symbol = str(symbol or "").strip().upper()
        side = str(side or "").strip().lower()
        if not order_id or not symbol:
            raise PositionMismatch("Order ID and symbol are required.")
        if side not in {"buy", "sell"}:
            raise PositionMismatch("Unsupported fill side.")

        try:
            cumulative = Decimal(str(cumulative_filled_qty))
        except (InvalidOperation, TypeError) as exc:
            raise PositionMismatch("Invalid cumulative fill quantity.") from exc
        if cumulative < 0:
            raise PositionMismatch("Cumulative fill quantity cannot be negative.")

        data = self._read()
        positions = data.get("_positions") if "_positions" in data else {
            key: value for key, value in data.items() if not key.startswith("_")
        }
        accounted = data.get("_accounted_fills", {})
        previous = Decimal(str(accounted.get(order_id, "0")))
        if cumulative < previous:
            raise PositionMismatch("Cumulative fill quantity regressed.")

        delta = cumulative - previous
        current = Decimal(str(positions.get(symbol, "0")))
        expected = current + (delta if side == "buy" else -delta)
        if expected < 0:
            raise PositionMismatch(
                f"Fill would create negative expected position for {symbol}."
            )

        positions[symbol] = str(expected)
        accounted[order_id] = str(cumulative)
        self._write({
            "_positions": positions,
            "_accounted_fills": accounted,
        })
        return expected, delta

    def set(self, symbol, quantity):
        symbol = str(symbol or "").strip().upper()
        if not symbol:
            raise PositionMismatch("Symbol is required.")
        try:
            quantity = Decimal(str(quantity))
        except (InvalidOperation, TypeError) as exc:
            raise PositionMismatch("Invalid expected position quantity.") from exc

        data = self._read()
        if "_positions" in data:
            data["_positions"][symbol] = str(quantity)
        else:
            data[symbol] = str(quantity)
        self._write(data)
        return quantity

    def get(self, symbol):
        symbol = str(symbol or "").strip().upper()
        data = self._read()
        positions = data.get("_positions", data)
        if symbol not in positions:
            return None
        try:
            return Decimal(str(positions[symbol]))
        except (InvalidOperation, TypeError) as exc:
            raise PositionMismatch(
                f"Invalid persisted position for {symbol}."
            ) from exc
