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
        capital_transition=None,
        position_allocation_book=None,
        sell_fill_checkpoints=None,
        sell_transition_journal=None,
        capital_fill_checkpoints=None,
    ):
        self.execution_engine = execution_engine
        self.order_journal = order_journal
        self.order_tracker = order_tracker
        self.fill_accounting = fill_accounting
        self.capital_lifecycle = capital_lifecycle
        self.capital_transition = capital_transition
        self.position_allocation_book = position_allocation_book
        self.sell_fill_checkpoints = sell_fill_checkpoints
        self.sell_transition_journal = sell_transition_journal
        self.capital_fill_checkpoints = capital_fill_checkpoints

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

        if self.capital_transition is not None and state.filled_qty:
            if state.filled_avg_price is None:
                raise RiskRejected("Filled order is missing average fill price.")
            if self.capital_fill_checkpoints is None:
                raise RiskRejected("Persistent capital fill checkpoint store is required.")
            cumulative_value = state.filled_qty * state.filled_avg_price
            delta_qty, delta_value = self.capital_fill_checkpoints.delta(
                state.order_id, state.filled_qty, cumulative_value
            )
            if state.side == "buy" and delta_qty > 0:
                allocation_id = f"buy:{state.order_id}:{state.filled_qty}"
                self.capital_transition.buy_fill(
                    client_order_id, allocation_id, delta_value, terminal=state.terminal
                )
                if self.position_allocation_book is None:
                    raise RiskRejected("Persistent position allocation book is required.")
                self.position_allocation_book.record_allocated_buy(
                    allocation_id, state.symbol, delta_qty, delta_value
                )
                self.capital_fill_checkpoints.commit(
                    state.order_id, state.filled_qty, cumulative_value
                )
            elif state.side == "sell" and delta_qty > 0:
                if self.position_allocation_book is None or self.sell_transition_journal is None:
                    raise RiskRejected("Persistent sell accounting components are required.")
                previous_qty = state.filled_qty - delta_qty
                self.sell_transition_journal.prepare(
                    state.order_id, state.symbol, previous_qty, state.filled_qty
                )
                self.position_allocation_book.release_sell(state.symbol, delta_qty)
                self.sell_transition_journal.mark_applied(state.order_id)
                self.capital_fill_checkpoints.commit(
                    state.order_id, state.filled_qty, cumulative_value
                )
                if self.sell_fill_checkpoints is not None:
                    self.sell_fill_checkpoints.commit(state.order_id, state.filled_qty)
                self.sell_transition_journal.complete(state.order_id)
        elif self.capital_lifecycle is not None:
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
