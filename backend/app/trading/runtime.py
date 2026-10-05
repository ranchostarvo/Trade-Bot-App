from dataclasses import dataclass


@dataclass(frozen=True)
class StartupReport:
    recovered_orders: int
    updated_orders: int
    terminal_orders: int
    open_orders: int
    ready: bool


class PaperTradingRuntime:
    def __init__(
        self,
        execution_engine,
        recovery_manager,
        kill_switch,
    ):
        self.execution_engine = execution_engine
        self.recovery_manager = recovery_manager
        self.kill_switch = kill_switch
        self._started = False

    def startup(self):
        # Fail closed: an engaged kill switch or failed reconciliation
        # prevents this runtime from becoming ready.
        self.kill_switch.validate()
        result = self.recovery_manager.reconcile_open_orders()
        self.kill_switch.validate()

        self._started = True
        return StartupReport(
            recovered_orders=result.checked,
            updated_orders=result.updated,
            terminal_orders=result.terminal,
            open_orders=result.open,
            ready=True,
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
