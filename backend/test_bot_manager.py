import tempfile
from pathlib import Path
from app.trading.bot_manager import BotManager
from app.trading.bot_registry import BotConfig, BotRegistry
from app.trading.kill_switch import KillSwitch

with tempfile.TemporaryDirectory() as root:
    registry=BotRegistry(Path(root)/"bots.json")
    registry.upsert(BotConfig("b1","stock","SPY","conservative",False))
    manager=BotManager(registry,KillSwitch())
    assert manager.set_enabled("b1",True).enabled
    assert manager.profile("b1").name=="conservative"
    manager.pause_all()
    assert not registry.get("b1").enabled
print("BOT MANAGER: PASS")
