from types import SimpleNamespace

from app.trading.runtime import PaperTradingRuntime


class FakeKillSwitch:
    def __init__(self):
        self.active = False
        self.reason = ""

    def validate(self):
        if self.active:
            raise RuntimeError(self.reason)
        return True


class FakeRecovery:
    def reconcile_open_orders(self):
        return SimpleNamespace(checked=2, updated=1, terminal=1, open=1)


class FakeExecution:
    def __init__(self):
        self.risk = SimpleNamespace(
            config=SimpleNamespace(trading_enabled=False, dry_run=True)
        )


kill = FakeKillSwitch()
runtime = PaperTradingRuntime(FakeExecution(), FakeRecovery(), kill)

before = runtime.status()
assert before.started is False
assert before.ready is False
assert before.trading_enabled is False
assert before.dry_run is True
assert before.open_orders == 0

report = runtime.startup()
assert report.ready is True
assert report.open_orders == 1

after = runtime.status()
assert after.started is True
assert after.ready is True
assert after.open_orders == 1

kill.active = True
kill.reason = "test stop"
blocked = runtime.status()
assert blocked.ready is False
assert blocked.kill_switch_active is True
assert blocked.kill_switch_reason == "test stop"

print("=== TRADING APP v2.0 / RUNTIME STATUS ===")
print("Pre-start fail-closed status: PASS")
print("Post-recovery ready status: PASS")
print("Kill-switch health reflection: PASS")
print("Trading remains disabled: PASS")
print("Dry-run remains enabled: PASS")
print("Broker interaction: NO")
print("RESULT: PASS")
