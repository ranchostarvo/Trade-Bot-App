from decimal import Decimal

from app.trading.portfolio import (
    ExposureConfig,
    ExposureRejected,
    PortfolioCoordinator,
)


def test_multiple_bots_share_symbol_limit():
    portfolio = PortfolioCoordinator(
        Decimal("100000"),
        ExposureConfig(
            max_symbol_notional=Decimal("2500"),
            max_symbol_pct=Decimal("10"),
        ),
    )
    for index in range(5):
        portfolio.reserve_exposure(
            f"bot-{index + 1}", "SPY", Decimal("500")
        )
    assert portfolio.symbol_exposure("SPY") == Decimal("2500")
    try:
        portfolio.reserve_exposure("bot-6", "SPY", Decimal("1"))
    except ExposureRejected:
        return
    raise AssertionError("Aggregate symbol limit was exceeded.")


def test_equity_percentage_limit_is_enforced():
    portfolio = PortfolioCoordinator(
        Decimal("10000"),
        ExposureConfig(
            max_symbol_notional=Decimal("5000"),
            max_symbol_pct=Decimal("10"),
        ),
    )
    portfolio.reserve_exposure("bot-1", "QQQ", Decimal("1000"))
    try:
        portfolio.reserve_exposure("bot-2", "QQQ", Decimal("1"))
    except ExposureRejected:
        return
    raise AssertionError("Symbol equity-percentage limit was exceeded.")


def test_release_reduces_aggregate_exposure():
    portfolio = PortfolioCoordinator(Decimal("100000"))
    portfolio.reserve_exposure("bot-1", "SPY", Decimal("500"))
    portfolio.reserve_exposure("bot-2", "SPY", Decimal("500"))
    remaining = portfolio.release_exposure(
        "bot-1", "SPY", Decimal("250")
    )
    assert remaining == Decimal("750")
    assert portfolio.symbol_exposure("SPY") == Decimal("750")


def test_symbol_normalization_prevents_duplicate_buckets():
    portfolio = PortfolioCoordinator(Decimal("100000"))
    portfolio.reserve_exposure("bot-1", "spy", Decimal("500"))
    portfolio.reserve_exposure("bot-2", "SPY", Decimal("500"))
    assert portfolio.snapshot() == {"SPY": "1000"}
