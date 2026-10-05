from decimal import Decimal

from app.trading.pipeline import ProposalPipeline
from app.trading.risk import RiskConfig, RiskEngine, RiskRejected
from app.trading.signal import MarketSnapshot, StrategyConfig, ThresholdStrategy


def test_hold_signal_proposes_no_order():
    pipeline = ProposalPipeline.development()
    result = pipeline.process(
        MarketSnapshot("SPY", Decimal("100"), Decimal("100"))
    )
    assert result["signal"] == "HOLD"
    assert result["order_proposed"] is False
    assert result["submitted"] is False


def test_buy_signal_reaches_dry_run_execution_only():
    pipeline = ProposalPipeline.development()
    result = pipeline.process(
        MarketSnapshot("SPY", Decimal("98"), Decimal("100"))
    )
    assert result["signal"] == "BUY"
    assert result["order_proposed"] is True
    assert result["status"] == "DRY_RUN"
    assert result["submitted"] is False


def test_sell_signal_fails_closed_without_reconciliation():
    pipeline = ProposalPipeline.development()
    try:
        pipeline.process(
            MarketSnapshot("SPY", Decimal("102"), Decimal("100"))
        )
    except RuntimeError as exc:
        assert "reconciliation is required" in str(exc)
        return
    raise AssertionError("Sell proceeded without broker reconciliation.")


def test_strategy_cannot_bypass_central_order_limit():
    strategy = ThresholdStrategy(
        StrategyConfig(proposed_notional=Decimal("600"))
    )
    pipeline = ProposalPipeline(
        strategy=strategy,
        execution=ProposalPipeline.development().execution,
    )
    try:
        pipeline.process(
            MarketSnapshot("SPY", Decimal("98"), Decimal("100"))
        )
    except RiskRejected:
        return
    raise AssertionError("Oversized strategy proposal bypassed risk engine.")


def test_trading_enabled_still_cannot_submit_to_broker():
    risk = RiskEngine(
        RiskConfig(trading_enabled=True, dry_run=False)
    )
    pipeline = ProposalPipeline.development(risk_engine=risk)
    try:
        pipeline.process(
            MarketSnapshot("SPY", Decimal("98"), Decimal("100"))
        )
    except RuntimeError as exc:
        assert "intentionally not implemented" in str(exc)
        return
    raise AssertionError("Broker submission unexpectedly became available.")
