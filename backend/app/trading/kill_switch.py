from dataclasses import dataclass


class KillSwitchActive(RuntimeError):
    pass


@dataclass
class KillSwitch:
    active: bool = False
    reason: str = ""
    store: object = None

    def __post_init__(self):
        if self.store is not None:
            state = self.store.load()

            self.active = state["kill_switch_active"]
            self.reason = state["kill_switch_reason"]

    def engage(self, reason: str):
        self.active = True
        self.reason = (
            reason.strip()
            or "Manual kill switch engaged."
        )

        if self.store is not None:
            self.store.save_kill_switch(
                True,
                self.reason,
            )

    def reset(self):
        self.active = False
        self.reason = ""

        if self.store is not None:
            self.store.save_kill_switch(
                False,
                "",
            )

    def validate(self):
        if self.active:
            raise KillSwitchActive(
                f"Trading disabled by kill switch: "
                f"{self.reason}"
            )

        return True
