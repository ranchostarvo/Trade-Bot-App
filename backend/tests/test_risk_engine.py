from decimal import Decimal

from app.trading.execution import ExecutionEngine
from app.trading.risk import OrderRequest, RiskRejected


def test_safe_order_is_dry_run():
    engine = ExecutionEngine()
    result = engine.execute(
        OrderRequest("SPY", "buy", Decimal("1"), Decimal("400"))
    )
    assert result["approved"] is True
    assert result["submitted"] is False
    assert result["status"] == "DRY_RUN"


def test_oversized_order_is_rejected():
    engine = ExecutionEngine()
    order = OrderRequest("SPY", "buy", Decimal("2"), Decimal("400"))
    try:
        engine.execute(order)
    except RiskRejected:
        return
    raise AssertionError("Oversized order was not rejected.")


def test_invalid_side_is_rejected():
    engine = ExecutionEngine()
    order = OrderRequest("SPY", "hold", Decimal("1"), Decimal("100"))
    try:
        engine.execute(order)
    except RiskRejected:
        return
    raise AssertionError("Invalid side was not rejected.")
