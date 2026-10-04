from dataclasses import dataclass


@dataclass
class KillSwitch:
    engaged: bool = False
    reason: str | None = None

    def engage(self, reason: str) -> None:
        self.engaged = True
        self.reason = reason

    def reset(self) -> None:
        self.engaged = False
        self.reason = None
