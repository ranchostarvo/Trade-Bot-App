import json
import os
from decimal import Decimal
from pathlib import Path


class FillCheckpointError(RuntimeError):
    pass


class FillCheckpointStore:
    """Persist the cumulative filled quantity already applied per broker order."""

    def __init__(self, path):
        self.path = Path(path)

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text())
            if not isinstance(data, dict):
                raise ValueError("checkpoint root must be an object")
            return data
        except Exception as exc:
            raise FillCheckpointError(
                f"Unable to read fill checkpoints: {exc}"
            ) from exc

    def get(self, order_id):
        value = self._read().get(str(order_id))
        if value is None:
            return Decimal("0")
        try:
            value = Decimal(str(value))
        except Exception as exc:
            raise FillCheckpointError(
                f"Invalid fill checkpoint for order {order_id}."
            ) from exc
        if value < 0:
            raise FillCheckpointError(
                f"Negative fill checkpoint for order {order_id}."
            )
        return value

    def set(self, order_id, cumulative_filled_qty):
        quantity = Decimal(str(cumulative_filled_qty))
        if quantity < 0:
            raise FillCheckpointError("Fill checkpoint cannot be negative.")

        data = self._read()
        key = str(order_id)
        previous = self.get(key)
        if quantity < previous:
            raise FillCheckpointError(
                f"Fill checkpoint regressed for order {order_id}."
            )

        data[key] = str(quantity)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, sort_keys=True, indent=2))
        os.replace(temporary, self.path)
        return quantity
