from decimal import Decimal

from .risk import RiskRejected


class SystemInvariantChecker:
    """Cross-component invariants that must hold before release."""

    def __init__(self, capital, exposure, registry, max_total_allocated):
        self.capital = capital
        self.exposure = exposure
        self.registry = registry
        self.max_total = Decimal(str(max_total_allocated))

    def check(self):
        reserved = Decimal(str(self.capital.allocated))
        invested = Decimal(str(self.exposure.total_invested))
        configured = len(self.registry.all())
        checks = {
            "nonnegative_reserved": reserved >= 0,
            "nonnegative_invested": invested >= 0,
            "combined_capital_ceiling": reserved + invested <= self.max_total,
            "bot_limit": configured <= 100,
        }
        failed = [name for name, ok in checks.items() if not ok]
        if failed:
            raise RiskRejected("System invariant failure: " + ", ".join(failed))
        return checks
