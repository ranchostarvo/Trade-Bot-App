from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from app.storage import SQLiteStore


def reserve(store, order, bot, amount="100"):
    return store.reserve_pending_exposure_with_limits(
        order, bot, "SPY", amount, "100000", "2500", "10"
    )


def test_pending_limit_counts_filled_exposure(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    for i in range(20):
        assert store.reserve_exposure_atomically(
            f"filled-{i}", "SPY", "100", "100000", "2500", "10"
        )
    for i in range(5):
        assert reserve(store, f"pending-{i}", f"bot-{i}")
    assert reserve(store, "overflow", "bot-overflow") is False


def test_concurrent_pending_orders_share_one_limit(tmp_path):
    path = tmp_path / "trading.db"

    def attempt(index):
        store = SQLiteStore(str(path))
        return reserve(store, f"order-{index}", f"bot-{index}")

    with ThreadPoolExecutor(max_workers=40) as pool:
        results = list(pool.map(attempt, range(100)))

    assert results.count(True) == 25
    assert results.count(False) == 75
    pending = SQLiteStore(str(path)).load_pending_exposure()
    total = sum(
        (Decimal(item["notional"]) for item in pending.values()),
        Decimal("0"),
    )
    assert total == Decimal("2500")
