from dataclasses import dataclass

from .position_reconciler import PositionMismatch


@dataclass(frozen=True)
class PositionRecoveryResult:
    checked: int
    matched: int


class PositionRecoveryManager:
    def __init__(self, reconciler, snapshot_store):
        self.reconciler = reconciler
        self.snapshot_store = snapshot_store

    def reconcile_expected_positions(self):
        data = self.snapshot_store._read()
        checked = 0
        matched = 0

        for symbol, expected in data.items():
            checked += 1
            try:
                self.reconciler.reconcile_expected(symbol, expected)
            except PositionMismatch:
                raise
            except Exception as exc:
                raise PositionMismatch(
                    f"Unable to reconcile expected position {symbol}: {exc}"
                ) from exc
            matched += 1

        return PositionRecoveryResult(checked=checked, matched=matched)
