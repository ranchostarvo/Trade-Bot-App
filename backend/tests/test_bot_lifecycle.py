from app.trading.lifecycle import BotLifecycle, BotState, InvalidTransition
from app.trading.registry import BotRegistry


def test_normal_lifecycle():
    bot = BotLifecycle("bot-1")
    assert bot.mark_ready() is BotState.READY
    assert bot.start() is BotState.RUNNING
    assert bot.pause() is BotState.PAUSED
    assert bot.start() is BotState.RUNNING
    assert bot.stop() is BotState.STOPPED


def test_cannot_start_created_bot():
    bot = BotLifecycle("bot-1")
    try:
        bot.start()
    except InvalidTransition:
        return
    raise AssertionError("CREATED bot started without becoming READY.")


def test_fault_requires_reason():
    bot = BotLifecycle("bot-1")
    try:
        bot.fault("")
    except InvalidTransition:
        return
    raise AssertionError("FAULTED state accepted without a reason.")


def test_registry_controls_100_bots():
    registry = BotRegistry()
    for index in range(100):
        bot = registry.create(f"bot-{index + 1}")
        bot.mark_ready()
        bot.start()
    assert len(registry.by_state(BotState.RUNNING)) == 100
    registry.stop_all()
    assert len(registry.by_state(BotState.STOPPED)) == 100
