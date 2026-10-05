from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.orchestrator import BotSpec, FleetOrchestrator
from app.trading.recovery import checkpoint_fleet, recover_fleet


def test_running_bots_recover_stopped_with_kill_switch(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    fleet = FleetOrchestrator(Decimal("1000"))
    fleet.provision(BotSpec("bot-1", Decimal("500")))
    fleet.start("bot-1")
    checkpoint_fleet(store, fleet)

    recovered = recover_fleet(store)
    status = recovered.status()
    assert status["running"] == 0
    assert status["stopped"] == 1
    assert status["kill_switch"] is True
    assert status["reserved_cash"] == "500"


def test_restart_requires_operator_reauthorization(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    fleet = FleetOrchestrator(Decimal("1000"))
    fleet.provision(BotSpec("bot-1", Decimal("500")))
    checkpoint_fleet(store, fleet)

    recovered = recover_fleet(store)
    try:
        recovered.start("bot-1")
    except RuntimeError:
        return
    raise AssertionError("Recovered bot started without re-authorization.")


def test_existing_kill_reason_survives_restart(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    fleet = FleetOrchestrator(Decimal("1000"))
    fleet.emergency_stop("daily loss limit")
    checkpoint_fleet(store, fleet)

    recovered = recover_fleet(store)
    assert recovered.kill_switch.engaged is True
    assert recovered.kill_switch.reason == "daily loss limit"
