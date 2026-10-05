import tempfile
from decimal import Decimal
from pathlib import Path

from app.trading.exposure_ledger import PortfolioExposureLedger
from app.trading.position_allocation import PositionAllocationBook
from app.trading.risk import RiskRejected

with tempfile.TemporaryDirectory() as root:
    root = Path(root)
    exposure = PortfolioExposureLedger(root / "exposure.json", Decimal("50000"))
    book = PositionAllocationBook(exposure, root / "allocations.json")
    book.record_buy("fill-a", "SPY", Decimal("1"), Decimal("500"))
    book.record_buy("fill-b", "SPY", Decimal("1"), Decimal("510"))
    assert exposure.total_invested == Decimal("1010")

    restarted = PositionAllocationBook(
        PortfolioExposureLedger(root / "exposure.json", Decimal("50000")),
        root / "allocations.json",
    )
    released = restarted.release_sell("SPY", Decimal("1.5"))
    assert released == Decimal("755")
    assert restarted.exposure.total_invested == Decimal("255")

    restarted2 = PositionAllocationBook(
        PortfolioExposureLedger(root / "exposure.json", Decimal("50000")),
        root / "allocations.json",
    )
    try:
        restarted2.release_sell("SPY", Decimal("0.6"))
        raise AssertionError("Oversell must fail closed.")
    except RiskRejected:
        pass
    assert restarted2.exposure.total_invested == Decimal("255")

print("PERSISTENT POSITION ALLOCATION: PASS")
print("FIFO cost-basis release: PASS")
print("Restart persistence: PASS")
print("Oversell fails closed: PASS")
print("Real Alpaca order submitted: NO")
