import json
import os
from decimal import Decimal
from pathlib import Path

from .risk import RiskRejected


class SellTransitionJournal:
    """Write-ahead journal for recoverable sell cost-basis transitions."""

    def __init__(self, path):
        self.path = Path(path)

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text())
            if not isinstance(raw, dict):
                raise ValueError("sell transition journal root must be an object")
            return raw
        except Exception as exc:
            raise RiskRejected(f"Unable to read sell transition journal: {exc}") from exc

    def _write(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, sort_keys=True, indent=2))
        os.replace(temporary, self.path)

    def prepare(self, order_id, symbol, from_qty, to_qty):
        key = str(order_id or "").strip()
        start = Decimal(str(from_qty))
        end = Decimal(str(to_qty))
        if not key or not symbol or start < 0 or end <= start:
            raise RiskRejected("Invalid sell transition.")
        data = self._read()
        existing = data.get(key)
        record = {
            "symbol": str(symbol).upper(),
            "from_qty": str(start),
            "to_qty": str(end),
            "status": "prepared",
        }
        if existing is not None and existing != record:
            raise RiskRejected("Conflicting sell transition already exists.")
        data[key] = record
        self._write(data)
        return record

    def mark_applied(self, order_id):
        data = self._read()
        key = str(order_id)
        if key not in data:
            raise RiskRejected("Prepared sell transition is missing.")
        data[key]["status"] = "applied"
        self._write(data)

    def complete(self, order_id):
        data = self._read()
        data.pop(str(order_id), None)
        self._write(data)

    def pending(self):
        return self._read()
