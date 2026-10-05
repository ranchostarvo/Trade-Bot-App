from dataclasses import dataclass

from .order_state import OrderState


class BrokerOrderStateRejected(RuntimeError):
    pass


BROKER_STATE_MAP = {
    "new": OrderState.ACKNOWLEDGED,
    "accepted": OrderState.ACKNOWLEDGED,
    "filled": OrderState.FILLED,
    "canceled": OrderState.CANCELED,
    "cancelled": OrderState.CANCELED,
    "rejected": OrderState.REJECTED,
}


@dataclass
class BrokerOrderReconciler:
    """Applies known broker terminal states to durable managed orders."""

    store: object
    settlement: object

    def reconcile(self, order_id: str, broker_status: str, bot_id, request):
        managed = self.store.load_managed_order(order_id)
        if managed is None:
            raise BrokerOrderStateRejected(
                f"Unknown managed order {order_id}."
            )

        normalized = (broker_status or "").strip().lower()
        target = BROKER_STATE_MAP.get(normalized)
        if target is None:
            raise BrokerOrderStateRejected(
                f"Unsupported broker order status: {broker_status!r}."
            )

        if target is OrderState.ACKNOWLEDGED:
            if managed.state is OrderState.SUBMITTED:
                managed.transition(OrderState.ACKNOWLEDGED)
                self.store.save_managed_order(managed)
            elif managed.state is not OrderState.ACKNOWLEDGED:
                raise BrokerOrderStateRejected(
                    f"Cannot acknowledge order from {managed.state.value}."
                )
            return managed

        if target is OrderState.FILLED:
            if managed.state is OrderState.SUBMITTED:
                managed.transition(OrderState.ACKNOWLEDGED)
            if managed.state is OrderState.ACKNOWLEDGED:
                managed.transition(OrderState.FILLED)
            elif managed.state is not OrderState.FILLED:
                raise BrokerOrderStateRejected(
                    f"Cannot fill order from {managed.state.value}."
                )
            self.store.save_managed_order(managed)
            if request.side.lower() == "buy":
                self.settlement.settle_buy(managed, bot_id, request)
            else:
                self.settlement.settle_sell(managed, bot_id, request)
            return managed

        if managed.state is not target:
            managed.transition(
                target,
                reason="Broker reported rejection."
                if target is OrderState.REJECTED
                else None,
            )
            self.store.save_managed_order(managed)
            self.settlement.settle_terminal(managed)
        return managed
