from copy import deepcopy
from decimal import Decimal


class VirtualBroker:
    """Deterministic paper-only broker for fast fault and lifecycle simulation."""

    def __init__(self):
        self.orders = {}
        self.positions = {}
        self.failures = []
        self.sequence = 0
        self.read_failures = []
        self.events = []
        self.prices = {}
        self.cash = Decimal("100000")
        self.equity = Decimal("100000")

    def inject(self, failure):
        self.failures.append(str(failure))

    def inject_read(self, failure):
        self.read_failures.append(str(failure))

    def set_price(self, symbol, price):
        value = Decimal(str(price))
        if value <= 0:
            raise ValueError("virtual price must be positive")
        self.prices[str(symbol).upper()] = value

    def _read_failure(self):
        failure = self.read_failures.pop(0) if self.read_failures else None
        if failure == "outage":
            raise ConnectionError("virtual broker read outage")
        if failure == "rate_limit":
            raise RuntimeError("virtual broker rate limit")

    def _failure(self):
        return self.failures.pop(0) if self.failures else None

    def submit_order(self, payload):
        failure = self._failure()
        if failure == "before_transmission":
            raise ConnectionError("virtual failure before transmission")

        self.sequence += 1
        order_id = f"virtual-{self.sequence:06d}"
        client_id = str(payload.get("client_order_id") or "")
        order = {
            "id": order_id,
            "client_order_id": client_id,
            "symbol": payload["symbol"],
            "side": payload["side"],
            "status": "accepted",
            "filled_qty": "0",
            "filled_avg_price": None,
        }
        self.orders[client_id] = order
        self.events.append({"type": "submitted", "client_order_id": client_id, "order_id": order_id})

        if failure == "after_transmission":
            raise TimeoutError("virtual ambiguous timeout after transmission")
        if failure == "reject":
            order["status"] = "rejected"
        return deepcopy(order)

    def get_order_by_client_id(self, client_order_id):
        self._read_failure()
        return deepcopy(self.orders[str(client_order_id)])

    def get_order(self, order_id):
        self._read_failure()
        for order in self.orders.values():
            if order["id"] == str(order_id):
                return deepcopy(order)
        raise KeyError(order_id)

    def transition(self, client_order_id, status, filled_qty="0", filled_avg_price=None):
        order = self.orders[str(client_order_id)]
        order["status"] = str(status).lower()
        order["filled_qty"] = str(filled_qty)
        order["filled_avg_price"] = (
            None if filled_avg_price is None else str(filled_avg_price)
        )
        self.events.append({"type": "transition", "client_order_id": str(client_order_id), "status": order["status"]})
        return deepcopy(order)

    def get_account(self):
        self._read_failure()
        return {"cash": str(self.cash), "equity": str(self.equity), "trading_blocked": False, "account_blocked": False}

    def get_position(self, symbol):
        self._read_failure()
        return deepcopy(self.positions.get(str(symbol).upper()))

    def expire_open_orders(self):
        terminal = {"filled", "canceled", "rejected", "expired"}
        expired = 0
        for order in self.orders.values():
            if order["status"] not in terminal:
                order["status"] = "expired"
                expired += 1
                self.events.append({"type": "expired", "client_order_id": order["client_order_id"]})
        return expired
