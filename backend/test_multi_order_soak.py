from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from app.trading.fill_accounting import FillAccounting
from app.trading.order_journal import OrderJournal
from app.trading.order_tracker import OrderState
from app.trading.position_snapshot import PositionSnapshotStore
from app.trading.recovery import RecoveryManager


class Tracker:
    def __init__(self, states):
        self.states = states

    def get(self, order_id):
        return self.states[order_id]


def state(order_id, symbol, side, status, qty, terminal=False):
    return OrderState(
        order_id=order_id,
        symbol=symbol,
        side=side,
        status=status,
        filled_qty=Decimal(qty),
        filled_avg_price=Decimal("100") if Decimal(qty) else None,
        terminal=terminal,
    )


with TemporaryDirectory() as directory:
    root = Path(directory)
    journal = OrderJournal(root / "orders.json")
    positions = PositionSnapshotStore(root / "positions.json")
    accounting = FillAccounting(positions)

    journal.record(state("spy-1", "SPY", "buy", "new", "0"))
    journal.record(state("qqq-1", "QQQ", "buy", "new", "0"))

    rounds = [
        {
            "spy-1": state("spy-1", "SPY", "buy", "partially_filled", "0.01"),
            "qqq-1": state("qqq-1", "QQQ", "buy", "partially_filled", "0.02"),
        },
        {
            "spy-1": state("spy-1", "SPY", "buy", "partially_filled", "0.01"),
            "qqq-1": state("qqq-1", "QQQ", "buy", "partially_filled", "0.03"),
        },
        {
            "spy-1": state("spy-1", "SPY", "buy", "filled", "0.02", True),
            "qqq-1": state("qqq-1", "QQQ", "buy", "filled", "0.04", True),
        },
    ]

    expected = [
        (Decimal("0.01"), Decimal("0.02")),
        (Decimal("0.01"), Decimal("0.03")),
        (Decimal("0.02"), Decimal("0.04")),
    ]

    for states, (spy_qty, qqq_qty) in zip(rounds, expected):
        RecoveryManager(Tracker(states), journal, accounting).reconcile_open_orders()
        assert positions.get("SPY") == spy_qty
        assert positions.get("QQQ") == qqq_qty

    # Once terminal, repeated restarts must leave both symbols unchanged.
    terminal = rounds[-1]
    for _ in range(25):
        result = RecoveryManager(
            Tracker(terminal), journal, accounting
        ).reconcile_open_orders()
        assert result.checked == 0
        assert positions.get("SPY") == Decimal("0.02")
        assert positions.get("QQQ") == Decimal("0.04")

print("=== TRADING APP v2.0 / MULTI-ORDER MULTI-SYMBOL SOAK ===")
print("Independent SPY accounting: PASS")
print("Independent QQQ accounting: PASS")
print("Interleaved incremental fills: PASS")
print("Duplicate fill replay isolation: PASS")
print("25 repeated terminal restarts: PASS")
print("Cross-symbol corruption: NONE")
print("Broker writes: NONE")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
