from copy import deepcopy


class VirtualBroker:
    """Deterministic paper-only broker for fast fault and lifecycle simulation."""

    def __init__(self):
        self.orders = {}
        self.positions = {}
        self.failures = []
        self.sequence = 0

    def inject(self, failure):
        self.failures.append(str(failure))

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

        if failure == "after_transmission":
            raise TimeoutError("virtual ambiguous timeout after transmission")
        if failure == "reject":
            order["status"] = "rejected"
        return deepcopy(order)

    def get_order_by_client_id(self, client_order_id):
        return deepcopy(self.orders[str(client_order_id)])

    def get_order(self, order_id):
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
        return deepcopy(order)
