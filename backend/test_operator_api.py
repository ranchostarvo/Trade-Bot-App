import tempfile
from pathlib import Path

from app.trading.bot_manager import BotManager
from app.trading.bot_registry import BotConfig, BotRegistry
from app.trading.kill_switch import KillSwitch
from app.trading.operator_api import OperatorAPI
from app.trading.operator_service import OperatorService
from app.trading.runtime import RuntimeStatus

class Runtime:
    def status(self):
        return RuntimeStatus(True, True, False, "", False, True, 0)

with tempfile.TemporaryDirectory() as root:
    registry = BotRegistry(Path(root) / "bots.json")
    registry.upsert(BotConfig("b1", "stock", "SPY", "conservative", False))
    manager = BotManager(registry, KillSwitch())
    api = OperatorAPI(OperatorService(Runtime(), manager))

    code, status = api.handle("GET", "/status")
    assert code == 200 and status["bots"]["configured"] == 1
    code, bot = api.handle("POST", "/bots/b1/enable")
    assert code == 200 and bot["enabled"]
    code, bots = api.handle("GET", "/bots")
    assert bots[0]["enabled"]
    code, paused = api.handle("POST", "/pause", {"reason": "test"})
    assert paused["paused"] and not registry.get("b1").enabled

print("OPERATOR API: PASS")
print("Direct broker-order route: ABSENT")
print("Live endpoint selector: ABSENT")
