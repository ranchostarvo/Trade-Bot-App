from .kill_switch import KillSwitch
from .risk import OrderRequest, RiskEngine, RiskRejected


class ExecutionEngine:
    def __init__(
        self,
        risk_engine=None,
        kill_switch=None,
        account_state_provider=None,
    ):
        self.risk = risk_engine or RiskEngine()
        self.kill_switch = kill_switch or KillSwitch()
        self.account_state_provider = account_state_provider

    def execute(self, order: OrderRequest):
        # 1. GLOBAL KILL SWITCH
        self.kill_switch.validate()

        # 2. FAIL-CLOSED ACCOUNT STATE REQUIREMENT
        if self.account_state_provider is None:
            raise RiskRejected(
                "Account risk-state provider is required."
            )

        try:
            account = self.account_state_provider.get_risk_state()
        except Exception as exc:
            raise RiskRejected(
                f"Unable to obtain valid account risk state: {exc}"
            ) from exc

        # 3. ORDER + DAILY LOSS RISK VALIDATION
        approval = self.risk.validate(
            order,
            account=account,
        )

        # 4. HARD DRY-RUN INTERLOCK
        if (
            self.risk.config.dry_run
            or not self.risk.config.trading_enabled
        ):
            return {
                **approval,
                "submitted": False,
                "status": "DRY_RUN",
            }

        # Broker execution deliberately unavailable.
        raise RuntimeError(
            "Broker submission is intentionally not implemented yet."
        )
