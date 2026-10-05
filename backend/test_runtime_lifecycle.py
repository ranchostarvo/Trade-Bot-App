from decimal import Decimal
from types import SimpleNamespace

from app.trading.order_tracker import OrderState
from app.trading.runtime import PaperTradingRuntime
from app.trading.risk import OrderRequest


class KillSwitch:
    active = False
    reason = ""

    def validate(self):
        return None


class Recovery:
    def reconcile_open_orders(self):
        return SimpleNamespace(checked=0, updated=0, terminal=0, open=0)


class PositionRecovery:
    def reconcile_expected_positions(self):
        return SimpleNamespace(checked=0, matched=0)


class Lifecycle:
    def __init__(self):
        self.calls = 0

    def submit(self, order, client_order_id):
        self.calls += 1
        return {
            "submitted": True,
            "status": "filled",
            "client_order_id": client_order_id,
        }


class Execution:
    risk = SimpleNamespace(
        config=SimpleNamespace(trading_enabled=False, dry_run=True)
    )

    def execute(self, order, client_order_id=None):
        raise AssertionError("Lifecycle service must own runtime execution.")


lifecycle = Lifecycle()
runtime = PaperTradingRuntime(
    execution_engine=Execution(),
    recovery_manager=Recovery(),
    kill_switch=KillSwitch(),
    position_recovery_manager=PositionRecovery(),
    lifecycle_service=lifecycle,
)

order = OrderRequest(
    symbol="SPY",
    side="buy",
    quantity=Decimal("0.01"),
    estimated_price=Decimal("770"),
)

try:
    runtime.execute(order, "runtime-test-1")
    raise AssertionError("Execution before startup must fail.")
except RuntimeError:
    pass

report = runtime.startup()
assert report.ready is True

result = runtime.execute(order, "runtime-test-1")
assert lifecycle.calls == 1
assert result["status"] == "filled"
assert result["client_order_id"] == "runtime-test-1"

print("=== TRADING APP v2.0 / RUNTIME LIFECYCLE ROUTING ===")
print("Pre-start execution blocked: PASS")
print("Startup recovery required: PASS")
print("Lifecycle service owns execution: PASS")
print("client_order_id propagated: PASS")
print("Direct execution bypassed: PASS")
print("Broker interaction: NO")
print("RESULT: PASS")
