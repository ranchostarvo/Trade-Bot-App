from app.trading.bot_orchestrator import BotOrder, BotOrchestrator
from app.trading.risk import RiskRejected


class Runtime:
    def __init__(self):
        self.calls = []
    def execute(self, order, client_order_id=None):
        self.calls.append(client_order_id)
        return {"submitted": False}


runtime = Runtime()
orchestrator = BotOrchestrator(runtime)
batch = [
    BotOrder(f"bot-{i}", object(), f"order-{i}")
    for i in range(99)
]
batch.append(BotOrder("bot-98", object(), "order-99"))

try:
    orchestrator.execute_batch(batch)
    raise AssertionError("Structurally invalid batch must fail.")
except RiskRejected:
    pass

assert runtime.calls == [], "Preflight failure must execute zero bots."

runtime = Runtime()
missing = [
    BotOrder("bot-1", object(), "order-1"),
    BotOrder("", object(), "order-2"),
]
try:
    BotOrchestrator(runtime).execute_batch(missing)
    raise AssertionError("Missing ID must fail.")
except RiskRejected:
    pass
assert runtime.calls == []

print("FULL-BATCH PREFLIGHT: PASS")
print("Late duplicate causes zero executions: PASS")
print("Missing ID causes zero executions: PASS")
print("Broker interaction: NONE")
print("Real Alpaca order submitted: NO")
