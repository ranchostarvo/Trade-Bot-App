from dataclasses import dataclass
from decimal import Decimal

from .execution import ExecutionEngine
from .kill_switch import KillSwitch
from .orchestrator import FleetOrchestrator
from .risk import RiskEngine


@dataclass
class TradingRuntime:
    """Composition root guaranteeing one global kill-switch dependency."""

    kill_switch: KillSwitch
    fleet: FleetOrchestrator
    risk: RiskEngine
    execution: ExecutionEngine

    @classmethod
    def build(cls, account_cash: Decimal, reconciler=None):
        kill_switch = KillSwitch()
        fleet = FleetOrchestrator(
            account_cash=account_cash,
            kill_switch=kill_switch,
        )
        risk = RiskEngine(kill_switch=kill_switch)
        execution = ExecutionEngine(
            risk_engine=risk,
            reconciler=reconciler,
        )
        return cls(
            kill_switch=kill_switch,
            fleet=fleet,
            risk=risk,
            execution=execution,
        )
