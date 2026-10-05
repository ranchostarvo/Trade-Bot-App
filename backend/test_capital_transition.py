import tempfile
from decimal import Decimal
from pathlib import Path

from app.trading.capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from app.trading.capital_transition import CapitalTransition
from app.trading.exposure_ledger import PortfolioExposureLedger
from app.trading.risk import RiskRejected

with tempfile.TemporaryDirectory() as root:
    root = Path(root)
    reservations = PortfolioCapitalCoordinator(
        CapitalConfig(max_total_allocated=Decimal("50000")),
        root / "reservations.json",
    )
    exposure = PortfolioExposureLedger(root / "exposure.json", Decimal("50000"))
    transition = CapitalTransition(reservations, exposure)

    reservations.reserve("order-1", Decimal("500"), Decimal("50000"))
    state = transition.buy_fill("order-1", "position-SPY", Decimal("200"))
    assert state["reserved_remaining"] == Decimal("300")
    assert reservations.get("order-1") == Decimal("300")
    assert exposure.get("position-SPY") == Decimal("200")

    # Finish the buy using a separate allocation ID for this fill.
    state = transition.buy_fill(
        "order-1", "position-SPY-fill-2", Decimal("300"), terminal=True
    )
    assert reservations.get("order-1") == Decimal("0")
    assert exposure.total_invested == Decimal("500")

    # A sell reduces invested exposure rather than touching an order reservation.
    released = transition.sell_fill("position-SPY", Decimal("125"))
    assert released == Decimal("125")
    assert exposure.total_invested == Decimal("375")

    # Restart preserves both sides of the accounting boundary.
    reservations2 = PortfolioCapitalCoordinator(
        CapitalConfig(max_total_allocated=Decimal("50000")),
        root / "reservations.json",
    )
    exposure2 = PortfolioExposureLedger(root / "exposure.json", Decimal("50000"))
    assert reservations2.total_allocated == Decimal("0")
    assert exposure2.total_invested == Decimal("375")

    try:
        transition.sell_fill("position-SPY", Decimal("1000"))
        raise AssertionError("Oversell release must fail closed.")
    except RiskRejected:
        pass

print("CAPITAL TRANSITIONS: PASS")
print("Partial buy: reserved -> invested: PASS")
print("Terminal buy retains invested exposure: PASS")
print("Sell releases invested exposure: PASS")
print("Restart persistence: PASS")
print("Oversell fails closed: PASS")
print("Real Alpaca order submitted: NO")
