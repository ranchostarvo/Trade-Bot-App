from dataclasses import replace

from .risk import RiskRejected
from .risk_profiles import get_risk_profile


class BotManager:
    """Persistent operator-facing bot configuration and safety controls."""

    def __init__(self, registry, kill_switch):
        self.registry = registry
        self.kill_switch = kill_switch

    def list_bots(self):
        return self.registry.all()

    def get(self, bot_id):
        bot = self.registry.get(bot_id)
        if bot is None:
            raise RiskRejected("Unknown bot.")
        return bot

    def set_enabled(self, bot_id, enabled):
        bot = self.get(bot_id)
        if enabled:
            self.kill_switch.validate()
            get_risk_profile(bot.risk_profile)
        return self.registry.upsert(replace(bot, enabled=bool(enabled)))

    def profile(self, bot_id):
        return get_risk_profile(self.get(bot_id).risk_profile)

    def pause_all(self, reason="operator pause"):
        self.kill_switch.engage(reason)
        for bot in list(self.registry.enabled()):
            self.registry.upsert(replace(bot, enabled=False))
        return len(self.registry.enabled())
