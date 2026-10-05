from app.trading.bot_orchestrator import BotOrder, BotOrchestrator
from app.trading.risk import RiskRejected


class Runtime:
    def __init__(self, reject_at):
        self.reject_at = reject_at
        self.calls = []
    def execute(self, order, client_order_id=None):
        self.calls.append(client_order_id)
        if client_order_id == self.reject_at:
            raise RiskRejected("simulated portfolio rejection")
        return {"submitted": False, "status": "DRY_RUN"}


batch = [
    BotOrder(f"bot-{i:03d}", object(), f"order-{i:03d}")
    for i in range(100)
]

runtime = Runtime("order-036")
results = BotOrchestrator(runtime).execute_batch(batch)
assert len(results) == 37
assert len(runtime.calls) == 37
assert results[-1]["bot_id"] == "bot-036"
assert results[-1]["ok"] is False
assert "portfolio rejection" in results[-1]["error"]
assert "order-037" not in runtime.calls

# Explicit non-fail-fast mode is available for controlled simulations only.
runtime = Runtime("order-036")
results = BotOrchestrator(runtime, stop_on_rejection=False).execute_batch(batch)
assert len(results) == 100
assert len(runtime.calls) == 100
assert sum(1 for item in results if not item["ok"]) == 1

print("=== 100-BOT FAIL-FAST CONTAINMENT ===")
print("Stops on first rejection by default: PASS")
print("Rejected bot identified: PASS")
print("Remaining bots not executed: PASS")
print("Explicit simulation continuation mode: PASS")
print("Broker interaction: NONE")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
