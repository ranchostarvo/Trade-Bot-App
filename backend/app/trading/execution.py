from .kill_switch import KillSwitch
from .risk import OrderRequest, RiskEngine, RiskRejected
from .submission_ledger import DuplicateOrder


class ExecutionEngine:
    def __init__(
        self,
        risk_engine=None,
        kill_switch=None,
        account_state_provider=None,
        broker=None,
        submission_ledger=None,
    ):
        self.risk = risk_engine or RiskEngine()
        self.kill_switch = kill_switch or KillSwitch()
        self.account_state_provider = account_state_provider
        self.broker = broker
        self.submission_ledger = submission_ledger

    def execute(self, order: OrderRequest, client_order_id=None):
        self.kill_switch.validate()

        if self.account_state_provider is None:
            raise RiskRejected("Account risk-state provider is required.")

        try:
            account = self.account_state_provider.get_risk_state()
        except Exception as exc:
            raise RiskRejected(
                f"Unable to obtain valid account risk state: {exc}"
            ) from exc

        approval = self.risk.validate(order, account=account)

        if self.risk.config.dry_run or not self.risk.config.trading_enabled:
            return {
                **approval,
                "submitted": False,
                "status": "DRY_RUN",
            }

        if self.broker is None:
            raise RiskRejected("Broker is required for enabled execution.")

        if self.submission_ledger is None:
            raise RiskRejected(
                "Persistent submission ledger is required for enabled execution."
            )

        client_order_id = str(client_order_id or "").strip()
        if not client_order_id:
            raise RiskRejected(
                "client_order_id is required for enabled execution."
            )

        fingerprint = "|".join([
            approval["symbol"],
            approval["side"],
            approval["quantity"],
            approval["estimated_price"],
            str(approval.get("requested_notional") or ""),
        ])

        try:
            self.submission_ledger.reserve(client_order_id, fingerprint)
        except DuplicateOrder as exc:
            raise RiskRejected(str(exc)) from exc
        except Exception as exc:
            raise RiskRejected(
                f"Unable to reserve order idempotency key: {exc}"
            ) from exc

        payload = {
            "symbol": approval["symbol"],
            "side": approval["side"],
            "type": "market",
            "time_in_force": "day",
            "client_order_id": client_order_id,
        }
        if approval.get("requested_notional") is not None:
            payload["notional"] = approval["requested_notional"]
        else:
            payload["qty"] = approval["quantity"]

        response = self.broker.submit_order(payload)

        return {
            **approval,
            "submitted": True,
            "status": response.get("status", "submitted"),
            "broker_order_id": response.get("id"),
            "client_order_id": client_order_id,
        }
