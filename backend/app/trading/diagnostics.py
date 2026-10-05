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
            }
        return data
