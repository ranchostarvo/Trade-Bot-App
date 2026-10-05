from dataclasses import dataclass

from app.trading.bot_orchestrator import BotOrder, BotOrchestrator
from app.trading.risk import RiskRejected


class Runtime:
    def __init__(self):
        self.calls = []
    def execute(self, order, client_order_id=None):
        self.calls.append((order, client_order_id))
        return {"submitted": False, "status": "DRY_RUN"}


runtime = Runtime()
orchestrator = BotOrchestrator(runtime, max_bots=100)
batch = [
    BotOrder(f"bot-{i:03d}", {"symbol": f"T{i:03d}"}, f"order-{i:03d}")
    for i in range(100)
]
results = orchestrator.execute_batch(batch)
assert len(results) == 100
assert len(runtime.calls) == 100
assert [call[1] for call in runtime.calls] == [
    f"order-{i:03d}" for i in range(100)
]

try:
    orchestrator.execute_batch(batch + [
        BotOrder("bot-100", {"symbol": "T100"}, "order-100")
    ])
    raise AssertionError("101-bot batch must fail closed.")
except RiskRejected:
    pass

for invalid in [
    [
        BotOrder("same", {}, "order-a"),
        BotOrder("same", {}, "order-b"),
    ],
    [
        BotOrder("bot-a", {}, "same-order"),
        BotOrder("bot-b", {}, "same-order"),
    ],
]:
    try:
        orchestrator.execute_batch(invalid)
        raise AssertionError("Duplicate identifiers must fail closed.")
    except RiskRejected:
        pass

print("=== 100-BOT ORCHESTRATOR ===")
print("100-bot bounded batch: PASS")
print("Deterministic sequential order: PASS")
print("101st bot rejected: PASS")
print("Duplicate bot ID rejected: PASS")
print("Duplicate client order ID rejected: PASS")
print("Broker interaction: NONE")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
