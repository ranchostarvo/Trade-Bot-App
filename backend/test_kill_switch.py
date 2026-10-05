from decimal import Decimal

from app.trading.execution import ExecutionEngine
from app.trading.kill_switch import (
    KillSwitch,
    KillSwitchActive,
)
from app.trading.risk import OrderRequest


print("=== TRADING APP v2.0 / KILL SWITCH TEST ===")

kill_switch = KillSwitch()
engine = ExecutionEngine(kill_switch=kill_switch)

order = OrderRequest(
    symbol="SPY",
    side="buy",
    quantity=Decimal("1"),
    estimated_price=Decimal("400"),
)

result = engine.execute(order)

assert result["submitted"] is False
assert result["status"] == "DRY_RUN"

print("Normal dry-run execution: PASS")

kill_switch.engage("Operator emergency stop")

assert kill_switch.active is True

try:
    engine.execute(order)
    raise AssertionError(
        "Order was allowed while kill switch was active."
    )
except KillSwitchActive:
    print("Active kill switch blocks order: PASS")

kill_switch.reset()

assert kill_switch.active is False

result = engine.execute(order)

assert result["submitted"] is False
assert result["status"] == "DRY_RUN"

print("Kill switch reset: PASS")
print("Broker submission remains blocked: PASS")
print("RESULT: PASS")
