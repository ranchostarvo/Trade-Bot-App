from dataclasses import dataclass


@dataclass(frozen=True)
class ReleaseGateReport:
    go: bool
    checks: dict
    blockers: tuple


class PaperV1ReleaseGate:
    """Machine-readable release gate; every required invariant must pass."""

    REQUIRED = (
        "ci_green",
        "runtime_recovery",
        "kill_switch",
        "daily_loss",
        "order_limit",
        "combined_capital",
        "idempotency",
        "market_session",
        "fill_accounting",
        "sell_recovery",
        "position_recovery",
        "hundred_bot_preflight",
        "hundred_bot_virtual_day",
        "paper_only_boundary",
        "system_invariants",
        "operator_api",
        "asset_analysis",
    )

    def assess(self, evidence):
        checks = {name: bool(evidence.get(name, False)) for name in self.REQUIRED}
        blockers = tuple(name for name, passed in checks.items() if not passed)
        return ReleaseGateReport(not blockers, checks, blockers)
