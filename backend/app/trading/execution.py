from .risk import OrderRequest, RiskEngine


class ExecutionEngine:
    def __init__(self, risk_engine=None):
        self.risk = risk_engine or RiskEngine()

    def execute(self, order: OrderRequest):
        approval = self.risk.validate(order)

        # HARD SAFETY INTERLOCK
        if (
            self.risk.config.dry_run
            or not self.risk.config.trading_enabled
        ):
            return {
                **approval,
                "submitted": False,
                "status": "DRY_RUN",
            }

        raise RuntimeError(
            "Live broker submission is intentionally not implemented yet."
        )
