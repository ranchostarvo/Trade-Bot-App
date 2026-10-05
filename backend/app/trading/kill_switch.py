from dataclasses import dataclass


@dataclass
class KillSwitch:
    engaged: bool = False
    reason: str | None = None

    def engage(self, reason: str) -> None:
        self.engaged = True
        self.reason = reason

    def reset(self, confirmation: str) -> None:
        if not self.engaged:
            raise RuntimeError("Kill switch is not engaged.")
        if confirmation != "CLEAR-KILL-SWITCH":
            raise RuntimeError("Explicit kill-switch confirmation is required.")
        self.engaged = False
        self.reason = None
