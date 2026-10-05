from decimal import Decimal

from app.trading.risk import (
    AccountRiskState,
    RiskEngine,
    RiskRejected,
)


engine = RiskEngine()

print("=== TRADING APP v2.0 / DAILY LOSS TEST ===")

safe_account = AccountRiskState(
    start_of_day_equity=Decimal("100000"),
    current_equity=Decimal("98000"),
)

safe_loss = engine.validate_daily_loss(safe_account)

assert safe_loss == Decimal("2.00")
print("2.00% daily loss allowed: PASS")

limit_account = AccountRiskState(
    start_of_day_equity=Decimal("100000"),
    current_equity=Decimal("97500"),
)

try:
    engine.validate_daily_loss(limit_account)
    raise AssertionError("2.5% daily loss was not blocked.")
except RiskRejected:
    print("2.50% daily loss blocked: PASS")

over_limit_account = AccountRiskState(
    start_of_day_equity=Decimal("100000"),
    current_equity=Decimal("97000"),
)

try:
    engine.validate_daily_loss(over_limit_account)
    raise AssertionError("3.0% daily loss was not blocked.")
except RiskRejected:
    print("3.00% daily loss blocked: PASS")

print("RESULT: PASS")
