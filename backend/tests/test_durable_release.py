from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.orchestrator import BotSpec, FleetOrchestrator
from app.trading.resources import DurableResourceCoordinator


def test_stopping_bot_releases_durable_capital(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    resources = DurableResourceCoordinator(
        store, Decimal("500"), Decimal("100000")
    )
    fleet = FleetOrchestrator(
        account_cash=Decimal("500"),
        resource_coordinator=resources,
    )
    fleet.provision(BotSpec("bot-1", Decimal("500")))
    assert store.load_capital_reservations() == {"bot-1": "500"}

    fleet.stop("bot-1")
    assert store.load_capital_reservations() == {}

    replacement = fleet.provision(BotSpec("bot-2", Decimal("500")))
    assert replacement.state.value == "READY"
