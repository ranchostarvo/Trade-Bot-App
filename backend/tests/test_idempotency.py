from concurrent.futures import ThreadPoolExecutor

from app.trading.idempotency import DuplicateOrder, IdempotencyRegistry


def test_duplicate_order_key_is_rejected():
    registry = IdempotencyRegistry()
    registry.reserve("order-123")
    try:
        registry.reserve("order-123")
    except DuplicateOrder:
        return
    raise AssertionError("Duplicate order key was accepted.")


def test_blank_order_key_is_rejected():
    try:
        IdempotencyRegistry().reserve("   ")
    except ValueError:
        return
    raise AssertionError("Blank idempotency key was accepted.")


def test_concurrent_duplicate_reservation_has_single_winner():
    registry = IdempotencyRegistry()

    def attempt(_):
        try:
            registry.reserve("same-order")
            return "accepted"
        except DuplicateOrder:
            return "duplicate"

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(attempt, range(100)))

    assert results.count("accepted") == 1
    assert results.count("duplicate") == 99
