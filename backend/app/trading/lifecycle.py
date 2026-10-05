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
    ):
        self.execution_engine = execution_engine
        self.order_journal = order_journal
        self.order_tracker = order_tracker
        self.fill_accounting = fill_accounting
        self.capital_lifecycle = capital_lifecycle
        self.capital_transition = capital_transition
        self.position_allocation_book = position_allocation_book
        self.sell_fill_checkpoints = sell_fill_checkpoints

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
            fill_notional = state.filled_qty * state.filled_avg_price
            allocation_id = f"{client_order_id}:{state.order_id}:{state.filled_qty}"
            if state.side == "buy":
                # Allocation identity is cumulative-fill specific, making
                # repeated observation of the same broker state idempotent.
                if (
                    self.position_allocation_book is None
                    or self.position_allocation_book.get(allocation_id) is None
                ):
                    self.capital_transition.buy_fill(
                        client_order_id,
                        allocation_id,
                        fill_notional,
                        terminal=state.terminal,
                    )
                    if self.position_allocation_book is not None:
                        self.position_allocation_book._positions[allocation_id] = __import__(
                            "app.trading.position_allocation",
                            fromlist=["PositionAllocation"],
                        ).PositionAllocation(
                            allocation_id, state.symbol, state.filled_qty, fill_notional
                        )
                        self.position_allocation_book._write()
            elif state.side == "sell":
                if self.position_allocation_book is None:
                    raise RiskRejected("Persistent position allocation book is required for sells.")
                if self.sell_fill_checkpoints is None:
                    raise RiskRejected("Persistent sell-fill checkpoint store is required.")
                delta_qty = self.sell_fill_checkpoints.delta(
                    state.order_id, state.filled_qty
                )
                if delta_qty > 0:
                    self.position_allocation_book.release_sell(
                        state.symbol, delta_qty
                    )
                    # Commit only after cost-basis release succeeds. A crash
                    # before this write remains fail-closed for reconciliation.
                    self.sell_fill_checkpoints.commit(
                        state.order_id, state.filled_qty
                    )
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
