from .order_tracker import OrderState
from .risk import RiskRejected


class OrderLifecycleService:
    def __init__(
        self,
        execution_engine,
        order_journal,
        order_tracker,
        fill_accounting,
        capital_lifecycle=None,
    ):
        self.execution_engine = execution_engine
        self.order_journal = order_journal
        self.order_tracker = order_tracker
        self.fill_accounting = fill_accounting
        self.capital_lifecycle = capital_lifecycle

    def submit(self, order, client_order_id):
        result = self.execution_engine.execute(
            order,
            client_order_id=client_order_id,
        )
        if not result.get("submitted"):
            return result

        order_id = str(result.get("broker_order_id") or "").strip()
        if not order_id:
            raise RiskRejected("Broker submission did not return an order ID.")

        state = self.order_tracker.get(order_id)
        self.order_journal.record(state)

        if state.filled_qty:
            self.fill_accounting.apply(state)

        if self.capital_lifecycle is not None:
            self.capital_lifecycle.reconcile(client_order_id, state)

        return {
            **result,
            "status": state.status,
            "filled_qty": str(state.filled_qty),
            "filled_avg_price": (
                str(state.filled_avg_price)
                if state.filled_avg_price is not None
                else None
            ),
            "terminal": state.terminal,
        }
