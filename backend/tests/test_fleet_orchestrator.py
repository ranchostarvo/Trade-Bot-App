from decimal import Decimal

from app.trading.lifecycle import BotState
from app.trading.orchestrator import BotSpec, FleetOrchestrator


def test_bot_requires_capital_before_ready():
    fleet = FleetOrchestrator(Decimal("500"))
    bot = fleet.provision(BotSpec("bot-1", Decimal("500")))
    assert bot.state is BotState.READY
    assert fleet.status()["available_cash"] == "0"


def test_100_bot_fleet_start_and_emergency_stop():
    fleet = FleetOrchestrator(Decimal("50000"))
    for index in range(100):
        bot_id = f"bot-{index + 1}"
        fleet.provision(BotSpec(bot_id, Decimal("500")))
        fleet.start(bot_id)

    assert fleet.status()["running"] == 100
    result = fleet.emergency_stop("operator emergency stop")
    assert result["stopped"] == 100
    assert fleet.status()["running"] == 0
    assert fleet.status()["kill_switch"] is True


def test_kill_switch_prevents_new_start():
    fleet = FleetOrchestrator(Decimal("1000"))
    fleet.provision(BotSpec("bot-1", Decimal("500")))
    fleet.emergency_stop("risk event")
    try:
        fleet.start("bot-1")
    except RuntimeError:
        return
    raise AssertionError("Bot started while kill switch was engaged.")


def test_overfunded_fleet_is_rejected():
    fleet = FleetOrchestrator(Decimal("500"))
    fleet.provision(BotSpec("bot-1", Decimal("500")))
    try:
        fleet.provision(BotSpec("bot-2", Decimal("1")))
    except Exception:
        return
    raise AssertionError("Fleet exceeded available account cash.")
