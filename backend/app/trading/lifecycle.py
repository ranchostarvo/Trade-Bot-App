from dataclasses import dataclass
from enum import Enum


class BotState(str, Enum):
    CREATED = "CREATED"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    FAULTED = "FAULTED"


class InvalidTransition(RuntimeError):
    """Raised when a bot lifecycle transition is not permitted."""


_ALLOWED = {
    BotState.CREATED: {BotState.READY, BotState.STOPPED, BotState.FAULTED},
    BotState.READY: {BotState.RUNNING, BotState.STOPPED, BotState.FAULTED},
    BotState.RUNNING: {BotState.PAUSED, BotState.STOPPED, BotState.FAULTED},
    BotState.PAUSED: {BotState.RUNNING, BotState.STOPPED, BotState.FAULTED},
    BotState.STOPPED: set(),
    BotState.FAULTED: {BotState.STOPPED},
}


@dataclass
class BotLifecycle:
    bot_id: str
    state: BotState = BotState.CREATED
    fault_reason: str | None = None

    def __post_init__(self):
        self.bot_id = self.bot_id.strip()
        if not self.bot_id:
            raise ValueError("bot_id is required.")

    def transition(self, target: BotState, reason: str | None = None) -> BotState:
        if target not in _ALLOWED[self.state]:
            raise InvalidTransition(
                f"Bot {self.bot_id} cannot transition "
                f"{self.state.value} -> {target.value}."
            )
        if target is BotState.FAULTED and not reason:
            raise InvalidTransition("FAULTED transition requires a reason.")
        self.state = target
        self.fault_reason = reason if target is BotState.FAULTED else None
        return self.state

    def mark_ready(self):
        return self.transition(BotState.READY)

    def start(self):
        return self.transition(BotState.RUNNING)

    def pause(self):
        return self.transition(BotState.PAUSED)

    def stop(self):
        return self.transition(BotState.STOPPED)

    def fault(self, reason: str):
        return self.transition(BotState.FAULTED, reason=reason)
