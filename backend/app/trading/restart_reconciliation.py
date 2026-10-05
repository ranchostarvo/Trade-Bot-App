from dataclasses import dataclass
from decimal import Decimal

from .risk import OrderRequest


class RestartReconciliationBlocked(RuntimeError):
    pass


@dataclass
class RestartBrokerReconciliation:
    """Self-contained read-only broker verification after restart."""

    store: object
    broker: object
    order_reconciler: object
    kill_switch: object

    def reconcile(self):
        unresolved = self.store.load_unresolved_orders()
        if not unresolved:
            return []

        self.kill_switch.engage(
            f"{len(unresolved)} unresolved broker order(s) require reconciliation."
        )
        failures = []

        for managed in unresolved:
            context = self.store.load_order_recovery_context(managed.order_id)
            if context is None:
                failures.append(f"{managed.order_id}:missing-context")
                continue
            broker_order_id = (context.get("broker_order_id") or "").strip()
            if not broker_order_id:
                failures.append(f"{managed.order_id}:missing-broker-order-id")
                continue
            try:
                request = OrderRequest(
                    symbol=context["symbol"],
                    side=context["side"],
                    quantity=Decimal(context["quantity"]),
                    estimated_price=Decimal(context["estimated_price"]),
                )
                status = self.broker.order_status(broker_order_id)
                self.order_reconciler.reconcile(
                    managed.order_id,
                    status,
                    context["bot_id"],
                    request,
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

        # Deliberately keep the kill switch engaged. Recovery is not
        # authorization to resume trading.
        return []
