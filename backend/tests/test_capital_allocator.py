from decimal import Decimal

from app.trading.capital import AllocationRejected, CapitalAllocator


def test_reservations_cannot_exceed_cash():
    allocator = CapitalAllocator(Decimal("1000"))
    allocator.reserve("bot-1", Decimal("500"))
    allocator.reserve("bot-2", Decimal("500"))
    try:
        allocator.reserve("bot-3", Decimal("1"))
    except AllocationRejected:
        assert allocator.available_cash == Decimal("0")
        return
    raise AssertionError("Allocator permitted an over-allocation.")


def test_release_returns_cash_to_pool():
    allocator = CapitalAllocator(Decimal("1000"))
    allocator.reserve("bot-1", Decimal("400"))
    allocator.release("bot-1")
    assert allocator.reserved_cash == Decimal("0")
    assert allocator.available_cash == Decimal("1000")


def test_same_bot_cannot_double_reserve():
    allocator = CapitalAllocator(Decimal("1000"))
    allocator.reserve("bot-1", Decimal("250"))
    try:
        allocator.reserve("bot-1", Decimal("250"))
    except AllocationRejected:
        assert allocator.reserved_cash == Decimal("250")
        return
    raise AssertionError("Duplicate bot reservation was accepted.")


def test_100_bots_share_one_cash_pool():
    allocator = CapitalAllocator(Decimal("50000"))
    for index in range(100):
        allocator.reserve(f"bot-{index + 1}", Decimal("500"))
    assert allocator.reserved_cash == Decimal("50000")
    assert allocator.available_cash == Decimal("0")
