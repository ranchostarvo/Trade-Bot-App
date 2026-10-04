from dataclasses import dataclass
from decimal import Decimal

from .capital import CapitalAllocator
from .kill_switch import KillSwitch
from .lifecycle import BotState
from .registry import BotRegistry


@dataclass(frozen=True)
class BotSpec:
    bot_id: str
    capital: Decimal


class FleetOrchestrator:
    """Coordinates lifecycle, capital, and the global emergency stop."""

    def __init__(
        self,
        account_cash: Decimal,
        registry=None,
        allocator=None,
        kill_switch=None,
    ):
        self.registry = registry or BotRegistry()
        self.allocator = allocator or CapitalAllocator(account_cash)
        self.kill_switch = kill_switch or KillSwitch()

    def provision(self, spec: BotSpec):
        if self.kill_switch.engaged:
            raise RuntimeError("Cannot provision while kill switch is engaged.")
        bot = self.registry.create(spec.bot_id)
        try:
            self.allocator.reserve(spec.bot_id, spec.capital)
            bot.mark_ready()
        except Exception:
            # Do not leave a half-provisioned bot with reserved capital.
            if spec.bot_id in {
                item.bot_id for item in self.registry.all()
            }:
                try:
                    bot.stop()
                except Exception:
                    pass
            raise
        return bot

    def start(self, bot_id: str):
        if self.kill_switch.engaged:
            raise RuntimeError("Cannot start bots while kill switch is engaged.")
        return self.registry.get(bot_id).start()

    def pause(self, bot_id: str):
        return self.registry.get(bot_id).pause()

    def stop(self, bot_id: str):
        bot = self.registry.get(bot_id)
        if bot.state is not BotState.STOPPED:
            bot.stop()
        try:
            self.allocator.release(bot_id)
        except Exception:
            pass
        return bot.state

    def emergency_stop(self, reason: str):
        if not reason.strip():
            raise ValueError("Emergency-stop reason is required.")
        self.kill_switch.engage(reason)
        self.registry.stop_all()
        return {
            "kill_switch": True,
            "reason": reason,
            "stopped": len(self.registry.by_state(BotState.STOPPED)),
        }

    def status(self):
        snapshot = self.allocator.snapshot()
        return {
            "bots": len(self.registry.all()),
            "running": len(self.registry.by_state(BotState.RUNNING)),
            "paused": len(self.registry.by_state(BotState.PAUSED)),
            "stopped": len(self.registry.by_state(BotState.STOPPED)),
            "kill_switch": self.kill_switch.engaged,
            "kill_reason": self.kill_switch.reason,
            "account_cash": str(snapshot.account_cash),
            "reserved_cash": str(snapshot.reserved_cash),
            "available_cash": str(snapshot.available_cash),
        }
