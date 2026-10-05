from dataclasses import dataclass


class StartupBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class StartupStatus:
    ready: bool
    kill_switch_engaged: bool
    reason: str | None = None


@dataclass
class StartupGate:
    """Fail-closed application startup gate for trading readiness."""

    runtime: object

    def evaluate(self) -> StartupStatus:
        recovery = getattr(self.runtime, "restart_recovery", None)
        if recovery is None:
            self.runtime.kill_switch.engage(
                "Restart reconciliation is unavailable."
            )
            return StartupStatus(
                ready=False,
                kill_switch_engaged=True,
                reason=self.runtime.kill_switch.reason,
            )

        try:
            recovery.reconcile()
        except Exception as exc:
            if not self.runtime.kill_switch.engaged:
                self.runtime.kill_switch.engage(
                    f"Startup recovery failed: {exc.__class__.__name__}"
                )
            return StartupStatus(
                ready=False,
                kill_switch_engaged=True,
                reason=self.runtime.kill_switch.reason,
            )

        if self.runtime.kill_switch.engaged:
            return StartupStatus(
                ready=False,
                kill_switch_engaged=True,
                reason=self.runtime.kill_switch.reason,
            )

        return StartupStatus(ready=True, kill_switch_engaged=False)
