from concurrent.futures import ThreadPoolExecutor

from app.storage import SQLiteStore
from app.trading.order_state import ManagedOrder, OrderState


def test_atomic_order_creation_writes_both_records(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    order = ManagedOrder("order-1")
    assert store.create_order_atomically(order, "order-1") is True
    assert store.has_order_key("order-1") is True
    assert store.load_managed_order("order-1").state == OrderState.CREATED


def test_duplicate_atomic_creation_writes_no_second_order(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    assert store.create_order_atomically(ManagedOrder("order-1"), "key-1")
    assert store.create_order_atomically(ManagedOrder("order-2"), "key-1") is False
    assert store.load_managed_order("order-2") is None


def test_concurrent_atomic_creation_has_single_winner(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))

    def attempt(index):
        return store.create_order_atomically(
            ManagedOrder(f"order-{index}"),
            "same-key",
        )

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(attempt, range(100)))

    assert results.count(True) == 1
    assert results.count(False) == 99
