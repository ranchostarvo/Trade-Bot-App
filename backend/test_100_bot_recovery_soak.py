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


def state(i, qty, terminal=False):
    return OrderState(
        order_id=f"bot-{i:03d}-order-1",
        symbol=f"T{i:03d}",
        side="buy",
        status="filled" if terminal else "partially_filled",
        filled_qty=Decimal(qty),
        filled_avg_price=Decimal("100"),
        terminal=terminal,
    )


BOT_COUNT = 100

with TemporaryDirectory() as directory:
    root = Path(directory)
    journal = OrderJournal(root / "orders.json")
    positions = PositionSnapshotStore(root / "positions.json")
    accounting = FillAccounting(positions)

    # Seed one independent open order for each simulated bot.
    for i in range(BOT_COUNT):
        initial = state(i, "0")
        initial = OrderState(
            order_id=initial.order_id,
            symbol=initial.symbol,
            side=initial.side,
            status="new",
            filled_qty=Decimal("0"),
            filled_avg_price=None,
            terminal=False,
        )
        journal.record(initial)

    # Round 1: every bot receives its first cumulative partial fill.
    first = {f"bot-{i:03d}-order-1": state(i, "0.01") for i in range(BOT_COUNT)}
    result = RecoveryManager(Tracker(first), journal, accounting).reconcile_open_orders()
    assert result.checked == BOT_COUNT
    for i in range(BOT_COUNT):
        assert positions.get(f"T{i:03d}") == Decimal("0.01")

    # Round 2: replay exactly the same broker state. No position may change.
    RecoveryManager(Tracker(first), journal, accounting).reconcile_open_orders()
    for i in range(BOT_COUNT):
        assert positions.get(f"T{i:03d}") == Decimal("0.01")

    # Round 3: all 100 orders complete at cumulative 0.02.
    final = {
        f"bot-{i:03d}-order-1": state(i, "0.02", True)
        for i in range(BOT_COUNT)
    }
    result = RecoveryManager(Tracker(final), journal, accounting).reconcile_open_orders()
    assert result.checked == BOT_COUNT
    assert result.terminal == BOT_COUNT
    for i in range(BOT_COUNT):
        assert positions.get(f"T{i:03d}") == Decimal("0.02")

    # Repeated restarts after terminal completion must remain inert.
    for _ in range(10):
        result = RecoveryManager(Tracker(final), journal, accounting).reconcile_open_orders()
        assert result.checked == 0
        for i in range(BOT_COUNT):
            assert positions.get(f"T{i:03d}") == Decimal("0.02")

print("=== TRADING APP v2.0 / 100-BOT RECOVERY SOAK ===")
print("Simulated bots: 100")
print("Independent symbols: 100")
print("Initial partial-fill recovery: PASS")
print("100-order duplicate replay: PASS")
print("100-order terminal recovery: PASS")
print("10 repeated full restart cycles: PASS")
print("Cross-bot position corruption: NONE")
print("Broker writes: NONE")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
