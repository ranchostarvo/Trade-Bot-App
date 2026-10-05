from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.orchestrator import BotSpec, FleetOrchestrator
from app.trading.resources import DurableResourceCoordinator, DurableResourceRejected


def test_fleet_provision_uses_durable_resource_gate(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    resources = DurableResourceCoordinator(
        store, Decimal("500"), Decimal("100000")
    )
    fleet = FleetOrchestrator(
        account_cash=Decimal("500"),
        resource_coordinator=resources,
    )

    bot = fleet.provision(BotSpec("bot-1", Decimal("500")))
    assert bot.state.value == "READY"
    assert store.load_capital_reservations() == {"bot-1": "500"}

    try:
        fleet.provision(BotSpec("bot-2", Decimal("500")))
    except DurableResourceRejected:
        return
    raise AssertionError("Fleet bypassed durable capital limit.")
