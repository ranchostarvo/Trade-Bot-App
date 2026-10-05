from dataclasses import dataclass

from app.trading.operator_api import OperatorAPI
from app.trading.risk import RiskRejected


@dataclass
class Bot:
    bot_id: str
    enabled: bool


class Manager:
    def __init__(self):
        self.items = [Bot("one", True), Bot("two", False)]
    def list_bots(self):
        return self.items
    def set_enabled(self, bot_id, enabled):
        for item in self.items:
            if item.bot_id == bot_id:
                item.enabled = enabled
                return item
        raise RiskRejected("Unknown bot.")
    def pause_all(self, reason):
        count = sum(1 for item in self.items if item.enabled)
        for item in self.items:
            item.enabled = False
        return count


class Service:
    def __init__(self):
        self.bot_manager = Manager()
    def status(self):
        return {"runtime": {"ready": True}}
    def bots(self):
        return [{"bot_id": b.bot_id, "enabled": b.enabled} for b in self.bot_manager.items]
    def release_readiness(self):
        return {"ready": True, "blockers": []}
    def set_bot_enabled(self, bot_id, enabled):
        bot = self.bot_manager.set_enabled(bot_id, enabled)
        return {"bot_id": bot.bot_id, "enabled": bot.enabled}


def run():
    api = OperatorAPI(Service())
    assert api.handle("GET", "/status")[0] == 200
    assert api.handle("GET", "/bots")[0] == 200
    assert api.handle("GET", "/readiness")[1]["ready"] is True
    assert api.handle("POST", "/bots/two/enable")[1]["enabled"] is True
    code, paused = api.handle("POST", "/pause", {"reason": "operator test"})
    assert code == 200
    assert paused["paused"] is True
    assert paused["enabled_bots"] == 2

    for method, path in [
        ("POST", "/orders"),
        ("POST", "/broker"),
        ("POST", "/live"),
        ("POST", "/kill-switch/bypass"),
    ]:
        try:
            api.handle(method, path)
            raise AssertionError(f"Unsafe route unexpectedly exposed: {path}")
        except RiskRejected:
            pass

    print("OPERATOR API PRODUCTION CONTRACT: PASS")


if __name__ == "__main__":
    run()
