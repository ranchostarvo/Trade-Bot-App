from dataclasses import dataclass

from .execution import ExecutionEngine
from .idempotency import DuplicateOrder
from .order_state import ManagedOrder, OrderState


@dataclass
class DurableExecutionWorkflow:
    """Coordinates durable lifecycle state with protected dry-run execution."""

    execution: ExecutionEngine
    store: object

    def process(self, order_id, request, account_state=None):
        if not order_id or not order_id.strip():
            raise ValueError("Order id is required.")

        existing = self.store.load_managed_order(order_id)
        if existing is not None:
            raise DuplicateOrder(
                f"Order {order_id} already exists in durable lifecycle state "
                f"{existing.state.value}."
            )

        managed = ManagedOrder(order_id)
        self.store.save_managed_order(managed)

        try:
            self.execution.risk.validate(request, account_state=account_state)
            managed.transition(OrderState.VALIDATED)
            self.store.save_managed_order(managed)

            # Execution owns the durable idempotency reservation and remaining
            # broker-bound validation. Broker submission is still disabled.
            result = self.execution.execute(
                request,
                account_state=account_state,
                idempotency_key=order_id,
            )
            managed.transition(OrderState.RESERVED)
            self.store.save_managed_order(managed)
            return {**result, "order_id": order_id, "order_state": managed.state.value}
        except Exception as exc:
            if not managed.terminal:
                managed.transition(OrderState.REJECTED, reason=str(exc))
                self.store.save_managed_order(managed)
            raise
