from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from app.trading.capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from app.trading.capital_lifecycle import CapitalLifecycle
from app.trading.order_tracker import OrderState
from app.trading.risk import RiskRejected


with TemporaryDirectory() as directory:
    path = Path(directory) / "capital.json"
    coordinator = PortfolioCapitalCoordinator(
        CapitalConfig(Decimal("50000"), Decimal("5000")), path
    )
    lifecycle = CapitalLifecycle(coordinator)
    coordinator.reserve("order-1", Decimal("500"), Decimal("50000"))

    partial = OrderState(
        "broker-1", "SPY", "buy", "partially_filled",
        Decimal("0.25"), Decimal("100"), False,
    )
    assert lifecycle.reconcile("order-1", partial) == Decimal("500")
    assert coordinator.get("order-1") == Decimal("500")

    # Restart must retain the conservative reservation.
    restarted = PortfolioCapitalCoordinator(
        CapitalConfig(Decimal("50000"), Decimal("5000")), path
    )
    assert restarted.get("order-1") == Decimal("500")

    terminal = OrderState(
        "broker-1", "SPY", "buy", "filled",
        Decimal("1"), Decimal("100"), True,
    )
    released = CapitalLifecycle(restarted).reconcile("order-1", terminal)
    assert released == Decimal("500")
    assert restarted.get("order-1") == Decimal("0")

    try:
        CapitalLifecycle(restarted).reconcile("missing", terminal)
        raise AssertionError("Missing expected reservation must fail closed.")
    except RiskRejected:
        pass

print("=== CAPITAL LIFECYCLE ===")
print("Partial fill keeps full reservation: PASS")
print("Reservation survives restart: PASS")
print("Terminal state releases reservation: PASS")
print("Missing reservation fails closed: PASS")
print("Broker writes: NONE")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
