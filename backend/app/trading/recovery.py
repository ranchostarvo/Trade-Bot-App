from decimal import Decimal

from .capital import CapitalAllocator
from .kill_switch import KillSwitch
from .lifecycle import BotState
from .orchestrator import FleetOrchestrator
from .registry import BotRegistry

STATE_KEY = "fleet_checkpoint"


def checkpoint_fleet(store, fleet: FleetOrchestrator) -> dict:
    reservations = {
        bot_id: str(amount)
        for bot_id, amount in fleet.allocator._reservations.items()
    }
    state = {
        "account_cash": str(fleet.allocator.snapshot().account_cash),
        "reservations": reservations,
        "bots": [
            {
                "bot_id": bot.bot_id,
                "previous_state": bot.state.value,
                "fault_reason": bot.fault_reason,
            }
            for bot in fleet.registry.all()
        ],
        "kill_switch": {
            "engaged": fleet.kill_switch.engaged,
            "reason": fleet.kill_switch.reason,
        },
    }
    store.set_state(STATE_KEY, state)
    return state


def recover_fleet(store) -> FleetOrchestrator | None:
    state = store.get_state(STATE_KEY)
    if state is None:
        return None

    allocator = CapitalAllocator(Decimal(state["account_cash"]))
    registry = BotRegistry()

    for bot_state in state["bots"]:
        bot = registry.create(bot_state["bot_id"])
        # Recovery is intentionally fail-closed. Never restore RUNNING.
        bot.stop()

    for bot_id, amount in state["reservations"].items():
        allocator.reserve(bot_id, Decimal(amount))

    prior_kill = state.get("kill_switch", {})
    reason = prior_kill.get("reason")
    if prior_kill.get("engaged"):
        recovery_reason = reason or "Kill switch was engaged before restart."
    else:
        recovery_reason = "Application restart requires operator re-authorization."

    kill_switch = KillSwitch(engaged=True, reason=recovery_reason)
    return FleetOrchestrator(
        account_cash=Decimal(state["account_cash"]),
        registry=registry,
        allocator=allocator,
        kill_switch=kill_switch,
    )
