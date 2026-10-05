from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from app.storage import SQLiteStore


def test_persistent_capital_reservations_survive_restart(tmp_path):
    path = tmp_path / "trading.db"
    store = SQLiteStore(str(path))
    assert store.reserve_capital_atomically("bot-1", "500", "50000")

    restarted = SQLiteStore(str(path))
    assert restarted.load_capital_reservations() == {"bot-1": "500"}


def test_multi_connection_capital_reservations_do_not_overdraw(tmp_path):
    path = tmp_path / "trading.db"

    def reserve(index):
        store = SQLiteStore(str(path))
        return store.reserve_capital_atomically(
            f"bot-{index}", Decimal("500"), Decimal("50000")
        )

    with ThreadPoolExecutor(max_workers=40) as pool:
        results = list(pool.map(reserve, range(200)))

    assert results.count(True) == 100
    reservations = SQLiteStore(str(path)).load_capital_reservations()
    total = sum((Decimal(v) for v in reservations.values()), Decimal("0"))
    assert total == Decimal("50000")
