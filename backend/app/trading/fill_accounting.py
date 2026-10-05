from decimal import Decimal

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

        current = self.snapshot_store.get(state.symbol)
        current = current if current is not None else Decimal("0")
        delta = state.filled_qty if state.side == "buy" else -state.filled_qty
        expected = current + delta

        if expected < 0:
            raise PositionMismatch(
                f"Fill would create negative expected position for {state.symbol}."
            )

        self.snapshot_store.set(state.symbol, expected)
        return expected
