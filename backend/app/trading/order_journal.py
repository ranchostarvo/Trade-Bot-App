import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .order_tracker import OrderState


class OrderJournal:
    def __init__(self, path):
        self.path = Path(path)

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Unable to read order journal: {exc}") from exc
        if not isinstance(data, dict):
            raise RuntimeError("Order journal must contain an object.")
        return data

    def record(self, state: OrderState):
        data = self._read()
        item = asdict(state)
        item["filled_qty"] = str(state.filled_qty)
        item["filled_avg_price"] = (
            str(state.filled_avg_price)
            if state.filled_avg_price is not None
            else None
        )
        item["observed_at"] = datetime.now(timezone.utc).isoformat()
        data[state.order_id] = item

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.flush()
        temp.replace(self.path)
        return item

    def get(self, order_id):
        return self._read().get(order_id)
