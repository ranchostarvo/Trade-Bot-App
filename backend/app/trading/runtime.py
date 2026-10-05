from dataclasses import dataclass


@dataclass(frozen=True)
class StartupReport:
    recovered_orders: int
    updated_orders: int
    terminal_orders: int
    open_orders: int
    ready: bool


@dataclass(frozen=True)
class RuntimeStatus:
    started: bool
    ready: bool
    kill_switch_active: bool
    kill_switch_reason: str
    trading_enabled: bool
    dry_run: bool
    open_orders: int


class PaperTradingRuntime:
    def __init__(self, execution_engine, recovery_manager, kill_switch):
        self.execution_engine = execution_engine
        self.recovery_manager = recovery_manager
        self.kill_switch = kill_switch
        self._started = False
        self._last_open_orders = 0

    def startup(self):
        self.kill_switch.validate()
        result = self.recovery_manager.reconcile_open_orders()
        self.kill_switch.validate()

        self._started = True
        self._last_open_orders = result.open
        return StartupReport(
            recovered_orders=result.checked,
            updated_orders=result.updated,
            terminal_orders=result.terminal,
            open_orders=result.open,
            ready=True,
        )

    def status(self):
        config = self.execution_engine.risk.config
        return RuntimeStatus(
            started=self._started,
            ready=self._started and not self.kill_switch.active,
            kill_switch_active=bool(self.kill_switch.active),
            kill_switch_reason=str(self.kill_switch.reason or ""),
            trading_enabled=bool(config.trading_enabled),
            dry_run=bool(config.dry_run),
            open_orders=self._last_open_orders,
        )

    def execute(self, order, client_order_id=None):
        if not self._started:
            raise RuntimeError(
                "Runtime startup reconciliation must complete before execution."
            )

        self.kill_switch.validate()
        return self.execution_engine.execute(
            order,
            client_order_id=client_order_id,
        )
