from dataclasses import dataclass


class KillSwitchActive(RuntimeError):
    pass


@dataclass
class KillSwitch:
    active: bool = False
    reason: str = ""

    def engage(self, reason: str):
        self.active = True
        self.reason = reason.strip() or "Manual kill switch engaged."

    def reset(self):
        self.active = False
        self.reason = ""

    def validate(self):
        if self.active:
            raise KillSwitchActive(
                f"Trading disabled by kill switch: {self.reason}"
            )

        return True
