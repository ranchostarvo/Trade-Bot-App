from dataclasses import dataclass

from .order_state import OrderState


class RestartReconciliationBlocked(RuntimeError):
    pass


@dataclass
class RestartBrokerReconciliation:
    """Read-only broker verification for unresolved orders after restart."""

    store: object
    broker: object
    order_reconciler: object
    kill_switch: object

    def reconcile(self, contexts):
        unresolved = self.store.load_unresolved_orders()
        if not unresolved:
            return []

        self.kill_switch.engage(
            f"{len(unresolved)} unresolved broker order(s) require reconciliation."
        )
        context_by_id = {item["order_id"]: item for item in contexts}
        failures = []

        for managed in unresolved:
            context = context_by_id.get(managed.order_id)
            if context is None:
                failures.append(f"{managed.order_id}:missing-context")
                continue
            try:
                status = self.broker.order_status(managed.order_id)
                self.order_reconciler.reconcile(
                    managed.order_id,
                    status,
                    context["bot_id"],
                    context["request"],
                )
            except Exception as exc:
                failures.append(
                    f"{managed.order_id}:{exc.__class__.__name__}"
                )

        remaining = self.store.load_unresolved_orders()
        if failures or remaining:
            details = ", ".join(failures) or ", ".join(
                f"{order.order_id}:{order.state.value}" for order in remaining
            )
            raise RestartReconciliationBlocked(
                f"Restart reconciliation incomplete: {details}"
            )

        # Deliberately do not reset the kill switch automatically.
        # An operator must explicitly reauthorize trading after recovery.
        return []
