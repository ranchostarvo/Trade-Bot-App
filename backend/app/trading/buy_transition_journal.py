import json
import os
from decimal import Decimal
from pathlib import Path

from .risk import RiskRejected


class BuyTransitionJournal:
    """Write-ahead journal for cross-ledger buy fill transitions."""

    def __init__(self, path):
        self.path = Path(path)
        self._entries = self._read()

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text())
            if not isinstance(raw, dict):
                raise ValueError("buy transition journal root must be an object")
            return raw
        except Exception as exc:
            raise RiskRejected(f"Unable to read buy transition journal: {exc}") from exc

    def _write(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(self._entries, sort_keys=True, indent=2))
        os.replace(temporary, self.path)

    def prepare(self, order_id, reservation_id, allocation_id, symbol, quantity, notional, terminal):
        key = str(order_id or "").strip()
        entry = {
            "reservation_id": str(reservation_id or "").strip(),
            "allocation_id": str(allocation_id or "").strip(),
            "symbol": str(symbol or "").strip().upper(),
            "quantity": str(Decimal(str(quantity))),
            "notional": str(Decimal(str(notional))),
            "terminal": bool(terminal),
            "status": "prepared",
        }
        if not key or not all(entry[k] for k in ("reservation_id", "allocation_id", "symbol")):
            raise RiskRejected("Valid buy transition identifiers are required.")
        if Decimal(entry["quantity"]) <= 0 or Decimal(entry["notional"]) <= 0:
            raise RiskRejected("Buy transition quantity and notional must be positive.")
        existing = self._entries.get(key)
        if existing is not None:
            comparable = dict(existing)
            comparable["status"] = "prepared"
            if comparable != entry:
                raise RiskRejected("Conflicting buy transition journal entry.")
            return existing
        self._entries[key] = entry
        self._write()
        return entry

    def mark_exposure_applied(self, order_id):
        self._set_status(order_id, "exposure_applied")

    def mark_allocation_applied(self, order_id):
        self._set_status(order_id, "allocation_applied")

    def complete(self, order_id):
        self._entries.pop(str(order_id), None)
        self._write()

    def pending(self):
        return {key: dict(value) for key, value in self._entries.items()}

    def _set_status(self, order_id, status):
        key = str(order_id)
        if key not in self._entries:
            raise RiskRejected("Buy transition journal entry is missing.")
        self._entries[key]["status"] = status
        self._write()
