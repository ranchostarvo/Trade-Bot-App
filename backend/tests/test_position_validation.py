from decimal import Decimal

from app.trading.position import (
    Position,
    PositionBook,
    PositionPolicy,
    PositionValidator,
)
from app.trading.risk import OrderRequest, RiskRejected


def order(side, quantity):
    return OrderRequest(
        symbol="SPY",
        side=side,
        quantity=Decimal(quantity),
        estimated_price=Decimal("100"),
    )


def test_buy_does_not_require_existing_position():
    PositionValidator(PositionBook()).validate(order("buy", "1"))


def test_sell_owned_quantity_is_allowed():
    validator = PositionValidator(
        PositionBook([Position("SPY", Decimal("5"))])
    )
    validator.validate(order("sell", "5"))


def test_sell_more_than_owned_is_rejected_by_default():
    validator = PositionValidator(
        PositionBook([Position("SPY", Decimal("2"))])
    )
    try:
        validator.validate(order("sell", "3"))
    except RiskRejected:
        return
    raise AssertionError("Short sale was allowed by default.")


def test_missing_position_rejects_sell():
    validator = PositionValidator(PositionBook())
    try:
        validator.validate(order("sell", "1"))
    except RiskRejected:
        return
    raise AssertionError("Sell without position was allowed.")


def test_short_selling_requires_explicit_policy():
    validator = PositionValidator(
        PositionBook(),
        PositionPolicy(allow_short_selling=True),
    )
    validator.validate(order("sell", "1"))
