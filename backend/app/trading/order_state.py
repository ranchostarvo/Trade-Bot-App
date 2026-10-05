from dataclasses import dataclass
from enum import Enum


class OrderState(str, Enum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    RESERVED = "RESERVED"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELED = "CANCELED"


TERMINAL_STATES = {
    OrderState.FILLED,
    OrderState.REJECTED,
    OrderState.CANCELED,
}

ALLOWED_TRANSITIONS = {
    OrderState.CREATED: {OrderState.VALIDATED, OrderState.REJECTED},
    OrderState.VALIDATED: {OrderState.RESERVED, OrderState.REJECTED},
    OrderState.RESERVED: {
        OrderState.SUBMITTED,
        OrderState.REJECTED,
        OrderState.CANCELED,
    },
    OrderState.SUBMITTED: {
        OrderState.ACKNOWLEDGED,
        OrderState.REJECTED,
        OrderState.CANCELED,
    },
    OrderState.ACKNOWLEDGED: {
        OrderState.FILLED,
        OrderState.REJECTED,
        OrderState.CANCELED,
    },
    OrderState.FILLED: set(),
    OrderState.REJECTED: set(),
    OrderState.CANCELED: set(),
}


@dataclass
class ManagedOrder:
    order_id: str
    state: OrderState = OrderState.CREATED
    reason: str | None = None

    def transition(self, target: OrderState, reason: str | None = None):
        if target not in ALLOWED_TRANSITIONS[self.state]:
            raise RuntimeError(
                f"Invalid order transition: {self.state.value} -> {target.value}"
            )
        if target == OrderState.REJECTED and not reason:
            raise RuntimeError("Rejected orders require a reason.")
        self.state = target
        self.reason = reason
        return self

    @property
    def terminal(self) -> bool:
        return self.state in TERMINAL_STATES
