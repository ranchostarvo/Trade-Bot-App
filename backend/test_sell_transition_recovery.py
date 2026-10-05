import tempfile
from decimal import Decimal
from pathlib import Path

from app.trading.exposure_ledger import PortfolioExposureLedger
from app.trading.position_allocation import PositionAllocationBook
from app.trading.risk import RiskRejected
from app.trading.sell_fill_checkpoint import SellFillCheckpointStore
from app.trading.sell_transition_journal import SellTransitionJournal
from app.trading.sell_transition_recovery import SellTransitionRecovery

with tempfile.TemporaryDirectory() as root:
    root = Path(root)
    exposure = PortfolioExposureLedger(root / "exposure.json", Decimal("50000"))
    book = PositionAllocationBook(exposure, root / "allocations.json")
    checkpoints = SellFillCheckpointStore(root / "sell_checkpoints.json")
    journal = SellTransitionJournal(root / "sell_journal.json")
    recovery = SellTransitionRecovery(journal, checkpoints, book)

    book.record_buy("buy-1", "SPY", Decimal("1"), Decimal("500"))

    # Crash after cost-basis release and mark-applied, before checkpoint.
    journal.prepare("sell-1", "SPY", Decimal("0"), Decimal("0.4"))
    book.release_sell("SPY", Decimal("0.4"))
    journal.mark_applied("sell-1")
    assert exposure.total_invested == Decimal("300")
    assert recovery.reconcile() == ["sell-1"]
    assert checkpoints.delta("sell-1", Decimal("0.4")) == 0
    assert exposure.total_invested == Decimal("300")
    assert journal.pending() == {}

    # A merely prepared transition is ambiguous: recovery must not guess.
    journal.prepare("sell-2", "SPY", Decimal("0"), Decimal("0.1"))
    try:
        recovery.reconcile()
        raise AssertionError("Ambiguous prepared transition must fail closed.")
    except RiskRejected:
        pass
    assert exposure.total_invested == Decimal("300")

print("SELL TRANSITION RECOVERY: PASS")
print("Applied transition replay: IDEMPOTENT")
print("Prepared ambiguity: FAIL CLOSED")
print("Double cost-basis release: PREVENTED")
print("Real Alpaca order submitted: NO")
