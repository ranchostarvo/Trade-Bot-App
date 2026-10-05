from dataclasses import dataclass
from decimal import Decimal

from .execution import ExecutionEngine
from .kill_switch import KillSwitch
from .orchestrator import FleetOrchestrator
from .resources import DurableResourceCoordinator
from .risk import RiskEngine
from .settlement import ExposureSettlement
from .broker_orders import BrokerOrderReconciler
from .restart_reconciliation import RestartBrokerReconciliation


@dataclass
class TradingRuntime:
    """Single composition root for shared trading safety dependencies."""

    kill_switch: KillSwitch
    fleet: FleetOrchestrator
    risk: RiskEngine
    execution: ExecutionEngine
    store: object = None
    resources: object = None
    settlement: object = None
    broker_orders: object = None
    restart_recovery: object = None

    @classmethod
    def build(
        cls,
        account_cash: Decimal,
        reconciler=None,
        store=None,
        account_equity: Decimal = None,
    ):
        kill_switch = KillSwitch()
        risk = RiskEngine(kill_switch=kill_switch)

        resources = None
        settlement = None
        broker_orders = None
        restart_recovery = None

        if store is not None:
            if account_equity is None:
                raise ValueError(
                    "account_equity is required when durable storage is enabled."
                )
            resources = DurableResourceCoordinator(
                store=store,
                account_cash=account_cash,
                account_equity=account_equity,
            )
            settlement = ExposureSettlement(resources)
            broker_orders = BrokerOrderReconciler(store, settlement)

        fleet = FleetOrchestrator(
            account_cash=account_cash,
            kill_switch=kill_switch,
            resource_coordinator=resources,
        )
        execution = ExecutionEngine(
            risk_engine=risk,
            reconciler=reconciler,
        )

        if store is not None and reconciler is not None:
            restart_recovery = RestartBrokerReconciliation(
                store=store,
                broker=reconciler,
                order_reconciler=broker_orders,
                kill_switch=kill_switch,
            )

        return cls(
            kill_switch=kill_switch,
            fleet=fleet,
            risk=risk,
            execution=execution,
            store=store,
            resources=resources,
            settlement=settlement,
            broker_orders=broker_orders,
            restart_recovery=restart_recovery,
        )
