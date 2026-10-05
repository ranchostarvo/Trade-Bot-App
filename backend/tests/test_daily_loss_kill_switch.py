from decimal import Decimal

from app.trading.kill_switch import KillSwitch
from app.trading.risk import (
    AccountRiskState,
    OrderRequest,
    RiskEngine,
    RiskRejected,
)


def order():
    return OrderRequest("SPY", "buy", Decimal("1"), Decimal("100"))


def test_below_daily_loss_limit_passes():
    switch = KillSwitch()
    engine = RiskEngine(kill_switch=switch)
    state = AccountRiskState(Decimal("10000"), Decimal("9800"))
    result = engine.validate(order(), state)
    assert result["approved"] is True
    assert switch.engaged is False


def test_daily_loss_limit_engages_kill_switch():
    switch = KillSwitch()
    engine = RiskEngine(kill_switch=switch)
    state = AccountRiskState(Decimal("10000"), Decimal("9750"))
    try:
        engine.validate(order(), state)
    except RiskRejected:
        assert switch.engaged is True
        assert "Daily loss limit" in switch.reason
        return
    raise AssertionError("2.5% daily loss was not rejected.")


def test_engaged_kill_switch_rejects_orders():
    switch = KillSwitch()
    switch.engage("manual emergency stop")
    engine = RiskEngine(kill_switch=switch)
    try:
        engine.validate(order())
    except RiskRejected as exc:
        assert "kill switch" in str(exc).lower()
        return
    raise AssertionError("Kill switch did not reject order.")
