from dataclasses import asdict


class OperatorService:
    """Thin contract layer for dashboard/API adapters."""

    def __init__(self, runtime, bot_manager, readiness=None):
        self.runtime = runtime
        self.bot_manager = bot_manager
        self.readiness = readiness

    def status(self):
        runtime = asdict(self.runtime.status())
        bots = self.bot_manager.list_bots()
        return {
            "runtime": runtime,
            "bots": {
                "configured": len(bots),
                "enabled": sum(1 for bot in bots if bot.enabled),
            },
        }

    def bots(self):
        return [asdict(bot) for bot in self.bot_manager.list_bots()]

    def set_bot_enabled(self, bot_id, enabled):
        return asdict(self.bot_manager.set_enabled(bot_id, enabled))

    def release_readiness(self):
        if self.readiness is None:
            return {"ready": False, "blockers": ["readiness_not_configured"]}
        report = self.readiness.assess()
        return {
            "ready": report.ready,
            "checks": report.checks,
            "blockers": list(report.blockers),
        }
