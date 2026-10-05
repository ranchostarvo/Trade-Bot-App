from decimal import Decimal
from tempfile import TemporaryDirectory
from pathlib import Path

from app.trading.position_snapshot import PositionSnapshotStore
from app.trading.position_reconciler import PositionMismatch, PositionReconciler


class Broker:
    def __init__(self, qty):
        self.qty = qty

    def get_position(self, symbol):
        return {
            "symbol": symbol,
            "qty": str(self.qty),
            "avg_entry_price": "770",
            "market_value": "10",
        }


with TemporaryDirectory() as directory:
    path = Path(directory) / "positions.json"
    store = PositionSnapshotStore(path)
    store.set("spy", Decimal("0.012978576"))

    restarted = PositionSnapshotStore(path)
    expected = restarted.get("SPY")
    assert expected == Decimal("0.012978576")

    matched = PositionReconciler(
        Broker("0.012978576")
    ).reconcile_expected("SPY", expected)
    assert matched.quantity == expected

    try:
        PositionReconciler(
            Broker("0.020000000")
        ).reconcile_expected("SPY", expected)
        raise AssertionError("Position mismatch must fail.")
    except PositionMismatch:
        pass

    path.write_text("{broken", encoding="utf-8")
    try:
        PositionSnapshotStore(path).get("SPY")
        raise AssertionError("Corrupt snapshot must fail closed.")
    except PositionMismatch:
        pass

print("=== TRADING APP v2.0 / EXPECTED POSITIONS ===")
print("Snapshot persistence: PASS")
print("Restart recovery: PASS")
print("Exact broker match: PASS")
print("Position mismatch rejected: PASS")
print("Corrupt snapshot fails closed: PASS")
print("Broker write interaction: NO")
print("RESULT: PASS")
