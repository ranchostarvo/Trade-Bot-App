from dataclasses import dataclass

from app.trading.runtime import PaperTradingRuntime


@dataclass
class RecoveryResult:
    checked: int = 1
    updated: int = 1
    terminal: int = 1
    open: int = 0


class KillSwitch:
    def __init__(self):
        self.calls = 0

    def validate(self):
        self.calls += 1


class Recovery:
    def __init__(self):
        self.calls = 0

    def reconcile_open_orders(self):
        self.calls += 1
        return RecoveryResult()


class Execution:
    def __init__(self):
        self.calls = 0

    def execute(self, order, client_order_id=None):
        self.calls += 1
        return {
            "submitted": False,
            "status": "DRY_RUN",
            "client_order_id": client_order_id,
        }


print("=== TRADING APP v2.0 / PAPER RUNTIME ORCHESTRATION ===")

kill = KillSwitch()
recovery = Recovery()
execution = Execution()
runtime = PaperTradingRuntime(execution, recovery, kill)

try:
    runtime.execute(object(), client_order_id="TEST-1")
    raise AssertionError("Execution was allowed before startup.")
except RuntimeError:
    print("Pre-start execution blocked: PASS")

report = runtime.startup()
assert report.ready is True
assert report.recovered_orders == 1
assert recovery.calls == 1
assert kill.calls == 2
print("Startup recovery completed: PASS")
print("Kill switch validated around recovery: PASS")

result = runtime.execute(object(), client_order_id="TEST-1")
assert result["submitted"] is False
assert execution.calls == 1
assert kill.calls == 3
print("Post-start controlled execution path: PASS")

print("Broker interaction: NO")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
