from .risk import OrderRequest, RiskEngine


class ExecutionEngine:
    def __init__(self, risk_engine=None):
        self.risk = risk_engine or RiskEngine()

    def execute(self, order: OrderRequest, account_state=None):
        approval = self.risk.validate(order, account_state=account_state)

        # Fail closed: broker submission is impossible until both controls
        # are explicitly changed in a later, separately tested milestone.
        if self.risk.config.dry_run or not self.risk.config.trading_enabled:
            return {
                **approval,
                "submitted": False,
                "status": "DRY_RUN",
            }

        raise RuntimeError(
            "Broker submission is intentionally not implemented yet."
        )
