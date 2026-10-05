import json
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from app.trading.capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from app.trading.risk import RiskRejected


config = CapitalConfig(
    max_total_allocated=Decimal("50000"),
    reserve_cash=Decimal("5000"),
)

with TemporaryDirectory() as directory:
    path = Path(directory) / "capital.json"

    first = PortfolioCapitalCoordinator(config, path)
    for i in range(10):
        first.reserve(f"bot-{i:03d}", Decimal("500"), Decimal("50000"))
    assert first.allocated == Decimal("5000")

    # Restart: reservations must survive and still count against the portfolio.
    restarted = PortfolioCapitalCoordinator(config, path)
    assert restarted.allocated == Decimal("5000")

    try:
        restarted.reserve("bot-000", Decimal("500"), Decimal("50000"))
        raise AssertionError("Restart must preserve duplicate reservation IDs.")
    except RiskRejected:
        pass

    restarted.release("bot-000")
    assert restarted.allocated == Decimal("4500")

    second_restart = PortfolioCapitalCoordinator(config, path)
    assert second_restart.allocated == Decimal("4500")
    assert second_restart.reserve(
        "bot-010", Decimal("500"), Decimal("50000")
    ) == Decimal("5000")

    # Corrupt persistence must fail closed rather than treating capital as free.
    path.write_text("{not-valid-json")
    try:
        PortfolioCapitalCoordinator(config, path)
        raise AssertionError("Corrupt reservation state must fail closed.")
    except RiskRejected:
        pass

with TemporaryDirectory() as directory:
    path = Path(directory) / "capital.json"
    path.write_text(json.dumps({"bot-bad": "-1"}))
    try:
        PortfolioCapitalCoordinator(config, path)
        raise AssertionError("Negative persisted reservation must fail closed.")
    except RiskRejected:
        pass

print("=== TRADING APP v2.0 / CAPITAL PERSISTENCE ===")
print("Reservations survive restart: PASS")
print("Duplicate protection survives restart: PASS")
print("Release survives restart: PASS")
print("Reused capital persists: PASS")
print("Corrupt state fails closed: PASS")
print("Invalid negative state fails closed: PASS")
print("Broker interaction: NONE")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
