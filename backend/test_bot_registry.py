import tempfile
from pathlib import Path

from app.trading.bot_registry import BotConfig, BotRegistry
from app.trading.risk import RiskRejected

with tempfile.TemporaryDirectory() as root:
    path = Path(root) / "bots.json"
    registry = BotRegistry(path)
    for i in range(100):
        registry.upsert(BotConfig(
            bot_id=f"bot-{i:03d}",
            asset_class=("stock", "etf", "crypto")[i % 3],
            symbol=f"T{i:03d}",
            risk_profile=("conservative", "moderate", "aggressive")[i % 3],
            enabled=(i % 2 == 0),
        ))
    assert len(registry.all()) == 100
    assert len(registry.enabled()) == 50
    restarted = BotRegistry(path)
    assert len(restarted.all()) == 100
    try:
        restarted.upsert(BotConfig("bot-100", "stock", "SPY", "conservative"))
        raise AssertionError("101st bot must fail closed")
    except RiskRejected:
        pass

with tempfile.TemporaryDirectory() as root:
    path = Path(root) / "bots.json"
    path.write_text("{bad json")
    try:
        BotRegistry(path)
        raise AssertionError("Corrupt registry must fail closed")
    except RiskRejected:
        pass

print("BOT REGISTRY: PASS")
print("100 persistent configs: PASS")
print("101st bot rejected: PASS")
print("Corrupt state fails closed: PASS")
print("Real Alpaca order submitted: NO")
