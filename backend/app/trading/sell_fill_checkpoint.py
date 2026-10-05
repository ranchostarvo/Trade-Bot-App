import json
import os
from decimal import Decimal
from pathlib import Path

from .risk import RiskRejected


class SellFillCheckpointStore:
    """Persistent cumulative sell-fill checkpoint keyed by broker order ID."""

    def __init__(self, path):
        self.path = Path(path)

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text())
            if not isinstance(raw, dict):
                raise ValueError("sell checkpoint root must be an object")
            parsed = {str(k): Decimal(str(v)) for k, v in raw.items()}
            if any(v < 0 for v in parsed.values()):
                raise ValueError("sell checkpoint cannot be negative")
            return parsed
        except Exception as exc:
            raise RiskRejected(f"Unable to read sell-fill checkpoints: {exc}") from exc

    def delta(self, order_id, cumulative_qty):
        key = str(order_id or "").strip()
        cumulative = Decimal(str(cumulative_qty))
        if not key or cumulative < 0:
            raise RiskRejected("Valid sell order ID and cumulative quantity are required.")
        data = self._read()
        previous = data.get(key, Decimal("0"))
        if cumulative < previous:
            raise RiskRejected("Cumulative sell fill quantity regressed.")
        return cumulative - previous

    def commit(self, order_id, cumulative_qty):
        key = str(order_id or "").strip()
        cumulative = Decimal(str(cumulative_qty))
        data = self._read()
        previous = data.get(key, Decimal("0"))
        if cumulative < previous:
            raise RiskRejected("Cumulative sell fill quantity regressed.")
        data[key] = cumulative
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps({k: str(v) for k, v in data.items()}, sort_keys=True, indent=2))
        os.replace(temporary, self.path)
        return cumulative
