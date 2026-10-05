from decimal import Decimal

from app.trading.buy_transition_journal import BuyTransitionJournal
from app.trading.buy_transition_recovery import BuyTransitionRecovery
from app.trading.capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from app.trading.capital_fill_checkpoint import CapitalFillCheckpointStore
from app.trading.exposure_ledger import PortfolioExposureLedger
from app.trading.position_allocation import PositionAllocationBook
from app.trading.risk import RiskRejected


def components(tmp_path):
    capital = PortfolioCapitalCoordinator(
        CapitalConfig(Decimal("50000"), Decimal("0")),
        tmp_path / "reservations.json",
    )
    exposure = PortfolioExposureLedger(tmp_path / "exposure.json", Decimal("50000"))
    positions = PositionAllocationBook(exposure, tmp_path / "positions.json")
    checkpoints = CapitalFillCheckpointStore(tmp_path / "capital_checkpoint.json")
    journal = BuyTransitionJournal(tmp_path / "buy_journal.json")
    recovery = BuyTransitionRecovery(
        journal, capital, exposure, positions, checkpoints
    )
    return capital, exposure, positions, checkpoints, journal, recovery


def test_prepared_without_exposure_fails_closed(tmp_path):
    _, _, _, _, journal, recovery = components(tmp_path)
    journal.prepare("o1", "c1", "a1", "SPY", Decimal("1"), Decimal("500"), False)

    try:
        recovery.reconcile()
        raise AssertionError("Expected ambiguous prepared transition to fail closed.")
    except RiskRejected as exc:
        assert "ambiguous" in str(exc)


def test_recovery_repairs_position_after_exposure_commit(tmp_path):
    _, exposure, positions, checkpoints, journal, recovery = components(tmp_path)
    journal.prepare("o1", "c1", "a1", "SPY", Decimal("1"), Decimal("500"), False)
    exposure.allocate("a1", Decimal("500"))

    try:
        recovery.reconcile()
        raise AssertionError("Expected missing checkpoint to fail closed.")
    except RiskRejected as exc:
        assert "checkpoint" in str(exc)

    allocation = positions.get("a1")
    assert allocation is not None
    assert allocation.quantity == Decimal("1")
    assert allocation.invested_notional == Decimal("500")


def test_allocation_applied_with_checkpoint_completes_restart(tmp_path):
    _, exposure, positions, checkpoints, journal, recovery = components(tmp_path)
    journal.prepare("o1", "c1", "a1", "SPY", Decimal("1"), Decimal("500"), True)
    exposure.allocate("a1", Decimal("500"))
    journal.mark_exposure_applied("o1")
    positions.record_allocated_buy("a1", "SPY", Decimal("1"), Decimal("500"))
    journal.mark_allocation_applied("o1")
    checkpoints.commit("o1", Decimal("1"), Decimal("500"))

    assert recovery.reconcile() == 1
    assert journal.pending() == {}
    assert exposure.total_invested == Decimal("500")
    assert positions.total_quantity("SPY") == Decimal("1")

    # A second restart is idempotent.
    assert recovery.reconcile() == 0


def test_conflicting_position_fails_closed(tmp_path):
    _, exposure, positions, _, journal, recovery = components(tmp_path)
    journal.prepare("o1", "c1", "a1", "SPY", Decimal("1"), Decimal("500"), False)
    exposure.allocate("a1", Decimal("500"))
    journal.mark_exposure_applied("o1")
    positions.record_allocated_buy("a1", "QQQ", Decimal("1"), Decimal("500"))

    try:
        recovery.reconcile()
        raise AssertionError("Expected conflicting allocation to fail closed.")
    except RiskRejected as exc:
        assert "conflicts" in str(exc)


if __name__ == "__main__":
    import tempfile
    from pathlib import Path

    tests = [
        test_prepared_without_exposure_fails_closed,
        test_recovery_repairs_position_after_exposure_commit,
        test_allocation_applied_with_checkpoint_completes_restart,
        test_conflicting_position_fails_closed,
    ]
    for test in tests:
        with tempfile.TemporaryDirectory() as directory:
            test(Path(directory))
    print("BUY TRANSITION CRASH RECOVERY: PASS")
