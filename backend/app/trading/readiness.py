from dataclasses import dataclass


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    checks: dict
    blockers: tuple


class PaperReadiness:
    """Read-only GO/NO-GO assessment for additional paper-order testing."""

    def __init__(self, runtime, diagnostics):
        self.runtime = runtime
        self.diagnostics = diagnostics

    def assess(self):
        snapshot = self.diagnostics.snapshot()
        runtime = snapshot["runtime"]
        recovery = snapshot.get("recovery", {})

        checks = {
            "runtime_started": bool(runtime.get("started")),
            "runtime_ready": bool(runtime.get("ready")),
            "kill_switch_clear": not bool(runtime.get("kill_switch_active")),
            "trading_enabled": bool(runtime.get("trading_enabled")),
            "dry_run_disabled": not bool(runtime.get("dry_run")),
            "no_open_orders": int(runtime.get("open_orders", 0)) == 0,
            "fill_checkpoint_enabled": bool(
                recovery.get("fill_checkpoint_enabled")
            ),
            "fill_accounting_enabled": bool(
                recovery.get("fill_accounting_enabled")
            ),
            "position_recovery_enabled": bool(
                recovery.get("position_recovery_enabled")
            ),
            "lifecycle_enabled": bool(
                recovery.get("lifecycle_enabled")
            ),
        }

        blockers = tuple(
            name for name, passed in checks.items() if not passed
        )
        return ReadinessReport(
            ready=not blockers,
            checks=checks,
            blockers=blockers,
        )
