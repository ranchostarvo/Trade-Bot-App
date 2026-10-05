from decimal import Decimal

from app.trading.capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from app.trading.capital_lifecycle import CapitalLifecycle
from app.trading.lifecycle import OrderLifecycleService
from app.trading.order_tracker import OrderState


class Execution:
    def execute(self, order, client_order_id=None):
        return {
            "submitted": True,
            "broker_order_id": "broker-1",
            "client_order_id": client_order_id,
        }


class Journal:
    def record(self, state):
        self.state = state


class Tracker:
    def __init__(self, state):
        self.state = state
    def get(self, order_id):
        return self.state


class FillAccounting:
    def apply(self, state):
        return None


capital = PortfolioCapitalCoordinator(
    CapitalConfig(Decimal("50000"), Decimal("5000"))
)
capital.reserve("client-1", Decimal("500"), Decimal("50000"))

partial = OrderState(
    "broker-1", "SPY", "buy", "partially_filled",
    Decimal("0.25"), Decimal("100"), False,
)
service = OrderLifecycleService(
    Execution(), Journal(), Tracker(partial), FillAccounting(),
    capital_lifecycle=CapitalLifecycle(capital),
)
result = service.submit(object(), "client-1")
assert result["terminal"] is False
assert capital.get("client-1") == Decimal("500")

terminal = OrderState(
    "broker-1", "SPY", "buy", "filled",
    Decimal("1"), Decimal("100"), True,
)
service = OrderLifecycleService(
    Execution(), Journal(), Tracker(terminal), FillAccounting(),
    capital_lifecycle=CapitalLifecycle(capital),
)
result = service.submit(object(), "client-1")
assert result["terminal"] is True
assert capital.get("client-1") == Decimal("0")

print("=== CAPITAL LIFECYCLE SERVICE INTEGRATION ===")
print("Partial order retains reservation: PASS")
print("Terminal order releases reservation: PASS")
print("Broker writes: SIMULATED ONLY")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
