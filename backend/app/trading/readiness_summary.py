class PaperReadinessSummary:
    """Translate readiness checks into concise operator-facing status."""

    LABELS = {
        "runtime_started": "Runtime startup has not completed.",
        "runtime_ready": "Runtime recovery is not ready.",
        "kill_switch_clear": "Global kill switch is active.",
        "trading_enabled": "Paper order transmission is disabled.",
        "dry_run_disabled": "Runtime is still in dry-run mode.",
        "no_open_orders": "An outstanding order must be reconciled first.",
        "fill_checkpoint_enabled": "Fill checkpoint protection is unavailable.",
        "fill_accounting_enabled": "Fill accounting is unavailable.",
        "position_recovery_enabled": "Position recovery is unavailable.",
        "lifecycle_enabled": "Order lifecycle management is unavailable.",
    }

    def render(self, report):
        blockers = [
            self.LABELS.get(name, name)
            for name in report.blockers
        ]
        return {
            "decision": "GO" if report.ready else "NO-GO",
            "ready": report.ready,
            "blocker_count": len(blockers),
            "blockers": blockers,
            "checks": dict(report.checks),
        }
