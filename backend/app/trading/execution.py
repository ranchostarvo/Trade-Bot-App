from .kill_switch import KillSwitch
from .risk import OrderRequest, RiskEngine, RiskRejected


class ExecutionEngine:
    def __init__(
        self,
        risk_engine=None,
        kill_switch=None,
        account_state_provider=None,
        broker=None,
    ):
        self.risk = risk_engine or RiskEngine()
        self.kill_switch = kill_switch or KillSwitch()
        self.account_state_provider = account_state_provider
        self.broker = broker

    def execute(self, order: OrderRequest):
        # 1. GLOBAL KILL SWITCH
        self.kill_switch.validate()

        # 2. FAIL-CLOSED ACCOUNT STATE
        if self.account_state_provider is None:
            raise RiskRejected(
                "Account risk-state provider is required."
            )

        try:
            account = (
                self.account_state_provider.get_risk_state()
            )
        except Exception as exc:
            raise RiskRejected(
                f"Unable to obtain valid account risk state: {exc}"
            ) from exc

        # 3. ORDER + DAILY-LOSS VALIDATION
        approval = self.risk.validate(
            order,
            account=account,
        )

        # 4. DEFAULT DRY-RUN INTERLOCK
        if (
            self.risk.config.dry_run
            or not self.risk.config.trading_enabled
        ):
            return {
                **approval,
                "submitted": False,
                "status": "DRY_RUN",
            }

        # 5. FAIL CLOSED IF EXECUTION IS ENABLED
        #    WITHOUT A BROKER.
        if self.broker is None:
            raise RiskRejected(
                "Broker is required for enabled execution."
            )

        # 6. CONSTRUCT PAPER ORDER
        payload = {
            "symbol": approval["symbol"],
            "qty": approval["quantity"],
            "side": approval["side"],
            "type": "market",
            "time_in_force": "day",
        }

        # AlpacaClient.submit_order() independently
        # refuses non-paper configuration.
        response = self.broker.submit_order(payload)

        return {
            **approval,
            "submitted": True,
            "status": response.get(
                "status",
                "submitted",
            ),
            "broker_order_id": response.get("id"),
        }
