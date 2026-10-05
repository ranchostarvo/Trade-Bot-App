from decimal import Decimal
from tempfile import TemporaryDirectory
from pathlib import Path

from app.trading.position_reconciler import PositionMismatch, PositionReconciler
from app.trading.position_recovery import PositionRecoveryManager
from app.trading.position_snapshot import PositionSnapshotStore


class Broker:
    def __init__(self, quantities):
        self.quantities = quantities

    def get_position(self, symbol):
        qty = self.quantities[symbol]
        return {
            "symbol": symbol,
            "qty": str(qty),
            "avg_entry_price": "100",
            "market_value": "100",
        }


with TemporaryDirectory() as directory:
    store = PositionSnapshotStore(Path(directory) / "positions.json")
    store.set("SPY", Decimal("1.25"))
    store.set("QQQ", Decimal("2"))

    manager = PositionRecoveryManager(
        PositionReconciler(Broker({"SPY": "1.25", "QQQ": "2"})),
        store,
    )
    result = manager.reconcile_expected_positions()
    assert result.checked == 2
    assert result.matched == 2

    mismatch = PositionRecoveryManager(
        PositionReconciler(Broker({"SPY": "1.25", "QQQ": "1.5"})),
        store,
    )
    try:
        mismatch.reconcile_expected_positions()
        raise AssertionError("Startup position mismatch must fail.")
    except PositionMismatch:
        pass

print("=== TRADING APP v2.0 / POSITION RECOVERY ===")
print("Persisted positions checked: PASS")
print("Exact positions matched: PASS")
print("Mismatch blocks recovery: PASS")
print("Broker write interaction: NO")
print("RESULT: PASS")
