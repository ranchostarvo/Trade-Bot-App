from dataclasses import dataclass

from .order_state import OrderState


class OrderRecoveryBlocked(RuntimeError):
    pass


@dataclass
class UnresolvedOrderRecovery:
    """Fail-closed restart gate for orders with uncertain broker outcome."""

    store: object
    kill_switch: object

    def inspect(self):
        unresolved = self.store.load_unresolved_orders()
        if unresolved:
            self.kill_switch.engage(
                f"{len(unresolved)} unresolved broker order(s) require reconciliation."
            )
        return unresolved

    def assert_clear(self):
        unresolved = self.inspect()
        if unresolved:
            states = ", ".join(
                f"{order.order_id}:{order.state.value}" for order in unresolved
            )
            raise OrderRecoveryBlocked(
                f"Trading blocked pending broker reconciliation: {states}"
            )
        return True
