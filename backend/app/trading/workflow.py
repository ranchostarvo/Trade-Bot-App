from dataclasses import dataclass

from .idempotency import DuplicateOrder
from .order_state import ManagedOrder, OrderState


@dataclass
class DurableExecutionWorkflow:
    """Coordinates durable lifecycle state with protected dry-run execution."""

    execution: object
    store: object

    def process(self, order_id, request, account_state=None):
        if not order_id or not order_id.strip():
            raise ValueError("Order id is required.")

        managed = ManagedOrder(order_id)
        if not self.store.create_order_atomically(managed, order_id):
            existing = self.store.load_managed_order(order_id)
            state = existing.state.value if existing is not None else "UNKNOWN"
            raise DuplicateOrder(
                f"Order {order_id} already exists in durable state {state}."
            )

        try:
            self.execution.risk.validate(request, account_state=account_state)
            managed.transition(OrderState.VALIDATED)
            self.store.save_managed_order(managed)

            # The order key was already reserved atomically with CREATED state.
            result = self.execution.execute(
                request,
                account_state=account_state,
                idempotency_key=order_id,
                idempotency_reserved=True,
            )

            managed.transition(OrderState.RESERVED)
            self.store.save_managed_order(managed)
            return {
                **result,
                "order_id": order_id,
                "order_state": managed.state.value,
                "idempotency_key": order_id,
            }
        except Exception as exc:
            if not managed.terminal:
                managed.transition(OrderState.REJECTED, reason=str(exc))
                self.store.save_managed_order(managed)
            raise
