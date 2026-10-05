from .position_reconciler import PositionMismatch


class FillAccounting:
    def __init__(self, snapshot_store):
        self.snapshot_store = snapshot_store

    def apply(self, state):
        if state.filled_qty < 0:
            raise PositionMismatch("Filled quantity cannot be negative.")
        if state.side not in {"buy", "sell"}:
            raise PositionMismatch("Unsupported fill side.")
        if not state.symbol:
            raise PositionMismatch("Fill symbol is required.")

        # Atomic position + cumulative-fill checkpoint. Re-observing the same
        # cumulative broker fill is idempotent and produces a zero delta.
        expected, _delta = self.snapshot_store.apply_fill_once(
            state.order_id,
            state.symbol,
            state.side,
            state.filled_qty,
        )
        return expected
