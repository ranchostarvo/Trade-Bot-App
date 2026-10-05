from decimal import Decimal
from tempfile import TemporaryDirectory
from pathlib import Path

from app.trading.position_snapshot import PositionSnapshotStore


with TemporaryDirectory() as tmp:
    store = PositionSnapshotStore(Path(tmp) / "positions.json")

    expected, delta = store.apply_fill_once(
        "paper-order-1", "SPY", "buy", Decimal("0.01")
    )
    assert expected == Decimal("0.01")
    assert delta == Decimal("0.01")

    # Simulate a crash immediately after the atomic state write, before
    # checkpoint/journal persistence. A restarted process sees the same
    # cumulative broker fill and must not apply it again.
    restarted = PositionSnapshotStore(Path(tmp) / "positions.json")
    expected, delta = restarted.apply_fill_once(
        "paper-order-1", "SPY", "buy", Decimal("0.01")
    )
    assert expected == Decimal("0.01")
    assert delta == Decimal("0")

    # A later incremental fill applies only the newly observed quantity.
    expected, delta = restarted.apply_fill_once(
        "paper-order-1", "SPY", "buy", Decimal("0.02")
    )
    assert expected == Decimal("0.02")
    assert delta == Decimal("0.01")

    # Replaying the latest cumulative fill remains idempotent.
    expected, delta = restarted.apply_fill_once(
        "paper-order-1", "SPY", "buy", Decimal("0.02")
    )
    assert expected == Decimal("0.02")
    assert delta == Decimal("0")

print("=== TRADING APP v2.0 / ATOMIC FILL CRASH RECOVERY ===")
print("Crash-window replay protection: PASS")
print("Incremental fill accounting: PASS")
print("Repeated cumulative fill idempotency: PASS")
print("Broker interaction: NONE")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
