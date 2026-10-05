from .position import PositionValidator
from .risk import OrderRequest, RiskEngine


class ExecutionEngine:
    def __init__(
        self,
        risk_engine=None,
        reconciler=None,
        idempotency_registry=None,
    ):
        self.risk = risk_engine or RiskEngine()
        self.reconciler = reconciler
        self.idempotency_registry = idempotency_registry

    def execute(
        self,
        order: OrderRequest,
        account_state=None,
        idempotency_key=None,
        idempotency_reserved=False,
    ):
        approval = self.risk.validate(order, account_state=account_state)

        # Sells fail closed unless a broker-backed position view is available.
        if order.side.lower() == "sell":
            if self.reconciler is None:
                raise RuntimeError(
                    "Broker position reconciliation is required for sells."
                )
            account, positions = self.reconciler.reconcile()
            if account.account_blocked or account.trading_blocked:
                raise RuntimeError("Broker account is blocked from trading.")
            PositionValidator(positions).validate(order)

        # A configured durable registry makes a unique logical order key
        # mandatory before the request can approach the broker boundary.
        if self.idempotency_registry is not None:
            if idempotency_key is None or not idempotency_key.strip():
                raise RuntimeError(
                    "Idempotency key is required for protected execution."
                )
            if idempotency_reserved:
                if not self.idempotency_registry.contains(idempotency_key):
                    raise RuntimeError(
                        "Claimed idempotency reservation does not exist."
                    )
            else:
                self.idempotency_registry.reserve(idempotency_key)

        # Fail closed: broker submission is impossible until both controls
        # are explicitly changed in a later, separately tested milestone.
        if self.risk.config.dry_run or not self.risk.config.trading_enabled:
            return {
                **approval,
                "submitted": False,
                "status": "DRY_RUN",
                "idempotency_key": idempotency_key,
            }

        raise RuntimeError(
            "Broker submission is intentionally not implemented yet."
        )
