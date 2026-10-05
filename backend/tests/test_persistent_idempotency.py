from concurrent.futures import ThreadPoolExecutor

from app.storage import SQLiteStore
from app.trading.idempotency import (
    DuplicateOrder,
    PersistentIdempotencyRegistry,
)


def test_idempotency_survives_restart(tmp_path):
    path = tmp_path / "trading.db"
    first = PersistentIdempotencyRegistry(SQLiteStore(str(path)))
    first.reserve("order-abc")

    restarted = PersistentIdempotencyRegistry(SQLiteStore(str(path)))
    assert restarted.contains("order-abc")
    try:
        restarted.reserve("order-abc")
    except DuplicateOrder:
        return
    raise AssertionError("Duplicate survived application restart.")


def test_persistent_concurrent_reservation_has_single_winner(tmp_path):
    registry = PersistentIdempotencyRegistry(
        SQLiteStore(str(tmp_path / "trading.db"))
    )

    def attempt(_):
        try:
            registry.reserve("same-persistent-order")
            return "accepted"
        except DuplicateOrder:
            return "duplicate"

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(attempt, range(100)))

    assert results.count("accepted") == 1
    assert results.count("duplicate") == 99
