from dataclasses import dataclass

from app.audit import AuditLog
from app.trading.startup import StartupGate


@dataclass
class ControlPlane:
    """Dependencies used by the control API."""

    runtime: object
    audit: AuditLog
    startup_status: object

    @classmethod
    def build(cls, runtime):
        audit = AuditLog(store=runtime.store) if runtime.store is not None else AuditLog()
        startup_status = StartupGate(runtime).evaluate()
        return cls(runtime=runtime, audit=audit, startup_status=startup_status)

    @property
    def fleet(self):
        return self.runtime.fleet

    @property
    def trading_ready(self) -> bool:
        return bool(self.startup_status.ready)
