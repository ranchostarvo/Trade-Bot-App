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
        bots = self.registry.all()
        configured = len(bots)
        bot_ids = [bot.bot_id for bot in bots]
        enabled = [bot for bot in bots if bot.enabled]
        checks = {
            "nonnegative_reserved": reserved >= 0,
            "nonnegative_invested": invested >= 0,
            "combined_capital_ceiling": reserved + invested <= self.max_total,
            "bot_limit": configured <= 100,
            "unique_bot_ids": len(bot_ids) == len(set(bot_ids)),
            "enabled_subset": len(enabled) <= configured,
            "capital_ceiling_positive": self.max_total > 0,
        }
        failed = [name for name, ok in checks.items() if not ok]
        if failed:
            raise RiskRejected("System invariant failure: " + ", ".join(failed))
        return checks
