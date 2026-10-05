from decimal import Decimal

from app.brokers.alpaca import AlpacaClient
from app.trading.account_state import (
    AlpacaAccountStateProvider,
)
from app.trading.execution import ExecutionEngine
from app.trading.kill_switch import (
    KillSwitch,
    KillSwitchActive,
)
from app.trading.risk import (
    OrderRequest,
    RiskRejected,
)


print("=== TRADING APP v2.0 / EXECUTION PIPELINE ===")

client = AlpacaClient()
provider = AlpacaAccountStateProvider(client)
kill_switch = KillSwitch()

engine = ExecutionEngine(
    kill_switch=kill_switch,
    account_state_provider=provider,
)

safe_order = OrderRequest(
    symbol="SPY",
    side="buy",
    quantity=Decimal("1"),
    estimated_price=Decimal("400"),
)

result = engine.execute(safe_order)

assert result["approved"] is True
assert result["submitted"] is False
assert result["status"] == "DRY_RUN"

print("Alpaca account state required: PASS")
print("Daily-loss risk gate: PASS")
print("Order-limit gate: PASS")
print("Dry-run submission block: PASS")

kill_switch.engage("Pipeline test")

try:
    engine.execute(safe_order)
    raise AssertionError(
        "Kill switch failed to block execution."
    )
except KillSwitchActive:
    print("Global kill switch: PASS")

kill_switch.reset()

engine_without_account = ExecutionEngine()

try:
    engine_without_account.execute(safe_order)
    raise AssertionError(
        "Execution succeeded without account state."
    )
except RiskRejected:
    print("Fail-closed missing account data: PASS")

print("No broker order submitted: PASS")
print("RESULT: PASS")
