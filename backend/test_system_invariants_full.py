from dataclasses import replace
from decimal import Decimal
import tempfile
from pathlib import Path

from app.trading.bot_registry import BotConfig, BotRegistry
from app.trading.capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from app.trading.exposure_ledger import PortfolioExposureLedger
from app.trading.risk import RiskRejected
from app.trading.system_invariants import SystemInvariantChecker


def rejected(fn, text):
    try:
        fn()
        raise AssertionError("Expected invariant rejection")
    except RiskRejected as exc:
        assert text in str(exc)


def run():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        capital = PortfolioCapitalCoordinator(
            CapitalConfig(Decimal("50000")), root / "capital.json"
        )
        exposure = PortfolioExposureLedger(root / "exposure.json", Decimal("50000"))
        registry = BotRegistry(root / "bots.json")
        for index in range(100):
            registry.upsert(BotConfig(
                f"bot-{index:03d}", "stock", f"SYM{index:03d}", "moderate",
                index % 2 == 0,
            ))

        checker = SystemInvariantChecker(capital, exposure, registry, Decimal("50000"))
        checks = checker.check()
        assert all(checks.values())

        exposure.allocate("existing", Decimal("49000"))
        capital.reserve("open", Decimal("1000"), Decimal("100000"), invested_capital=Decimal("49000"))
        assert all(checker.check().values())

        # Corrupt in-memory state deliberately to prove fail-closed behavior at
        # the cross-component boundary. Production mutation APIs prohibit this.
        capital._reservations["corrupt"] = Decimal("1")
        rejected(checker.check, "combined_capital_ceiling")
        capital._reservations.pop("corrupt")

        checker.max_total = Decimal("0")
        rejected(checker.check, "capital_ceiling_positive")

    print("SYSTEM-WIDE INVARIANTS: PASS")


if __name__ == "__main__":
    run()
