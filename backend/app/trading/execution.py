from .kill_switch import KillSwitch
from .risk import AccountRiskState, OrderRequest, RiskEngine


class ExecutionEngine:
    def __init__(self, risk_engine=None, kill_switch=None):
        self.risk = risk_engine or RiskEngine()
        self.kill_switch = kill_switch or KillSwitch()

    def execute(
        self,
        order: OrderRequest,
        account: AccountRiskState | None = None,
    ):
        # Kill switch is checked BEFORE normal order validation.
        self.kill_switch.validate()

        approval = self.risk.validate(
            order,
            account=account,
        )

        # HARD SAFETY INTERLOCK:
        # Broker submission remains impossible while dry_run
        # is enabled or trading_enabled is false.
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
            "Broker submission is intentionally not implemented yet."
        )
