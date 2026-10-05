from decimal import Decimal

from app.trading.pipeline import MarketProposalService, ProposalPipeline
from app.trading.signal import MarketSnapshot


class FakeMarketData:
    def __init__(self, snapshot):
        self._snapshot = snapshot
        self.requested = []

    def snapshot(self, symbol):
        self.requested.append(symbol)
        return self._snapshot


def test_symbol_flows_market_data_to_strategy_and_dry_run():
    provider = FakeMarketData(
        MarketSnapshot("SPY", Decimal("98"), Decimal("100"))
    )
    service = MarketProposalService(provider, ProposalPipeline.development())

    result = service.evaluate_symbol("SPY")

    assert provider.requested == ["SPY"]
    assert result["symbol"] == "SPY"
    assert result["signal"] == "BUY"
    assert result["order_proposed"] is True
    assert result["status"] == "DRY_RUN"
    assert result["submitted"] is False


def test_hold_market_snapshot_never_creates_order():
    provider = FakeMarketData(
        MarketSnapshot("QQQ", Decimal("100"), Decimal("100"))
    )
    service = MarketProposalService(provider, ProposalPipeline.development())

    result = service.evaluate_symbol("QQQ")

    assert result["signal"] == "HOLD"
    assert result["order_proposed"] is False
    assert result["submitted"] is False
    assert result["status"] == "NO_ACTION"
