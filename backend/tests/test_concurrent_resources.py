from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from app.trading.capital import AllocationRejected, CapitalAllocator
from app.trading.portfolio import ExposureRejected, PortfolioCoordinator


def test_concurrent_capital_reservations_never_overdraw():
    allocator = CapitalAllocator(Decimal("50000"))

    def reserve(index):
        try:
            allocator.reserve(f"bot-{index}", Decimal("500"))
            return True
        except AllocationRejected:
            return False

    with ThreadPoolExecutor(max_workers=40) as pool:
        results = list(pool.map(reserve, range(200)))

    assert results.count(True) == 100
    assert allocator.reserved_cash == Decimal("50000")
    assert allocator.available_cash == Decimal("0")


def test_concurrent_symbol_exposure_never_exceeds_limit():
    portfolio = PortfolioCoordinator(Decimal("100000"))

    def reserve(index):
        try:
            portfolio.reserve_exposure(
                f"bot-{index}", "SPY", Decimal("100")
            )
            return True
        except ExposureRejected:
            return False

    with ThreadPoolExecutor(max_workers=40) as pool:
        results = list(pool.map(reserve, range(100)))

    assert results.count(True) == 25
    assert portfolio.symbol_exposure("SPY") == Decimal("2500")
