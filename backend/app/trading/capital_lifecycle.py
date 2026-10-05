from decimal import Decimal

from .risk import RiskRejected


class CapitalLifecycle:
    """Reconcile open-order capital without freeing ambiguous exposure."""

    def __init__(self, coordinator):
        self.coordinator = coordinator

    def reconcile(self, client_order_id, state, original_quantity=None):
        reserved = self.coordinator.get(client_order_id)
        if reserved <= 0:
            raise RiskRejected("Expected capital reservation is missing.")

        if state.terminal:
            return self.coordinator.release(client_order_id)

        # Non-terminal orders remain conservatively reserved.  We intentionally
        # do not estimate remaining notional from market prices here: doing so
        # could release capital while broker exposure still exists.
        return reserved
