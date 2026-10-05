from decimal import Decimal

from app.trading.capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from app.trading.risk import RiskRejected

capital = PortfolioCapitalCoordinator(
    CapitalConfig(max_total_allocated=Decimal("50000"))
)
capital.reserve("last-slot", Decimal("500"), Decimal("100000"), invested_capital=Decimal("49500"))
assert capital.allocated == Decimal("500")

try:
    capital.reserve("overflow", Decimal("1"), Decimal("100000"), invested_capital=Decimal("49500"))
    raise AssertionError("Combined commitment ceiling must reject overflow.")
except RiskRejected:
    pass

capital.release("last-slot")
try:
    capital.reserve("no-room", Decimal("1"), Decimal("100000"), invested_capital=Decimal("50000"))
    raise AssertionError("Fully invested portfolio must reject new buy reservation.")
except RiskRejected:
    pass

print("COMBINED PORTFOLIO COMMITMENT: PASS")
print("Invested + reserved <= $50,000: PASS")
print("Fully invested blocks new reservation: PASS")
print("Real Alpaca order submitted: NO")
