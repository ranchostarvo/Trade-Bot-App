from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.resources import DurableResourceCoordinator, DurableResourceRejected


def coordinator(path):
    return DurableResourceCoordinator(
        SQLiteStore(str(path)),
        account_cash=Decimal("50000"),
        account_equity=Decimal("100000"),
    )


def test_coordinator_reservations_survive_new_runtime(tmp_path):
    path = tmp_path / "trading.db"
    first = coordinator(path)
    first.reserve_bot_capital("bot-1", Decimal("500"))
    first.reserve_symbol_exposure("bot-1", "SPY", Decimal("100"))

    second = coordinator(path)
    assert second.store.load_capital_reservations()["bot-1"] == "500"
    assert second.store.load_exposure_reservations("SPY")["bot-1"] == "100"


def test_many_runtime_instances_share_capital_limit(tmp_path):
    path = tmp_path / "trading.db"

    def attempt(index):
        try:
            coordinator(path).reserve_bot_capital(
                f"bot-{index}", Decimal("500")
            )
            return True
        except DurableResourceRejected:
            return False

    with ThreadPoolExecutor(max_workers=40) as pool:
        results = list(pool.map(attempt, range(200)))

    assert results.count(True) == 100
    assert results.count(False) == 100
