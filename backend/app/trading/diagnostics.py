from dataclasses import asdict


class RuntimeDiagnostics:
    def __init__(self, runtime, paths=None):
        self.runtime = runtime
        self.paths = paths

    def snapshot(self):
        status = self.runtime.status()
        risk = self.runtime.execution_engine.risk.config
        data = {
            "runtime": asdict(status),
            "risk_limits": {
                "max_order_notional": str(risk.max_order_notional),
                "max_daily_loss_pct": str(risk.max_daily_loss_pct),
            },
        }
        if self.paths is not None:
            data["state_files"] = {
                "risk_state": str(self.paths.risk_state),
                "equity_baseline": str(self.paths.equity_baseline),
                "order_journal": str(self.paths.order_journal),
                "submission_ledger": str(self.paths.submission_ledger),
                "position_snapshot": str(self.paths.position_snapshot),
                "fill_checkpoint": str(self.paths.fill_checkpoint),
            }
        recovery = self.runtime.recovery_manager
        data["recovery"] = {
            "fill_checkpoint_enabled": (
                getattr(recovery, "fill_checkpoint_store", None) is not None
            ),
            "fill_accounting_enabled": (
                getattr(recovery, "fill_accounting", None) is not None
            ),
            "position_recovery_enabled": (
                getattr(self.runtime, "position_recovery_manager", None) is not None
            ),
            "lifecycle_enabled": (
                getattr(self.runtime, "lifecycle_service", None) is not None
            ),
        }
        return data
