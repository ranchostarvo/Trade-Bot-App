from decimal import Decimal

from app.trading.capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from app.trading.risk import RiskRejected


coordinator = PortfolioCapitalCoordinator(
    CapitalConfig(
        max_total_allocated=Decimal("50000"),
        reserve_cash=Decimal("5000"),
    )
)

# 100 bots can each reserve the existing $500 per-order ceiling only when
# portfolio cash and the aggregate ceiling permit it.
for i in range(90):
    total = coordinator.reserve(
        f"bot-{i:03d}",
        Decimal("500"),
        Decimal("50000"),
    )
assert total == Decimal("45000")
assert coordinator.allocated == Decimal("45000")

# Reserve cash prevents the 91st $500 reservation.
try:
    coordinator.reserve("bot-090", Decimal("500"), Decimal("50000"))
    raise AssertionError("Reserve cash must block over-allocation.")
except RiskRejected:
    pass

assert coordinator.allocated == Decimal("45000")

# Releasing one bot's reservation makes exactly that capital available again.
assert coordinator.release("bot-000") == Decimal("500")
assert coordinator.allocated == Decimal("44500")
assert coordinator.reserve(
    "bot-090", Decimal("500"), Decimal("50000")
) == Decimal("45000")

# Duplicate IDs fail closed and cannot silently double reserve.
try:
    coordinator.reserve("bot-090", Decimal("500"), Decimal("50000"))
    raise AssertionError("Duplicate reservation must fail closed.")
except RiskRejected:
    pass

assert coordinator.allocated == Decimal("45000")

print("=== TRADING APP v2.0 / 100-BOT CAPITAL COORDINATION ===")
print("Aggregate allocation ceiling: PASS")
print("Portfolio reserve cash: PASS")
print("90 x $500 reservations: PASS")
print("91st reservation blocked: PASS")
print("Reservation release/reuse: PASS")
print("Duplicate reservation blocked: PASS")
print("Broker interaction: NONE")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
