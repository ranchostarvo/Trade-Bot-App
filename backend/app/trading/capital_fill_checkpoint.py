import json
import os
from decimal import Decimal
from pathlib import Path

from .risk import RiskRejected


class CapitalFillCheckpointStore:
    """Tracks cumulative broker fill quantity and value for delta accounting."""

    def __init__(self, path):
        self.path = Path(path)

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text())
            if not isinstance(data, dict):
                raise ValueError('checkpoint root must be an object')
            return data
        except Exception as exc:
            raise RiskRejected('Unable to read capital fill checkpoint.') from exc

    def recovery_state(self, order_id):
        key = str(order_id or '').strip()
        if not key:
            raise RiskRejected('Capital fill checkpoint ID is required.')
        item = self._read().get(key)
        if item is None:
            return None
        return (
            Decimal(str(item['quantity'])),
            Decimal(str(item['value'])),
        )

    def delta(self, order_id, quantity, value):
        key = str(order_id or '').strip()
        quantity = Decimal(str(quantity))
        value = Decimal(str(value))
        if not key or quantity < 0 or value < 0:
            raise RiskRejected('Invalid capital fill checkpoint.')
        previous = self._read().get(key, {'quantity': '0', 'value': '0'})
        old_quantity = Decimal(str(previous['quantity']))
        old_value = Decimal(str(previous['value']))
        if quantity < old_quantity or value < old_value:
            raise RiskRejected('Capital fill checkpoint regressed.')
        return quantity - old_quantity, value - old_value

    def commit(self, order_id, quantity, value):
        key = str(order_id or '').strip()
        quantity = Decimal(str(quantity))
        value = Decimal(str(value))
        self.delta(key, quantity, value)
        data = self._read()
        data[key] = {'quantity': str(quantity), 'value': str(value)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + '.tmp')
        temporary.write_text(json.dumps(data, sort_keys=True, indent=2))
        os.replace(temporary, self.path)