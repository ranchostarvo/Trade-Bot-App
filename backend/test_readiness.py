from types import SimpleNamespace

from app.trading.readiness import PaperReadiness


class Diagnostics:
    def __init__(self, snapshot):
        self._snapshot = snapshot

    def snapshot(self):
        return self._snapshot


def snapshot(**runtime_overrides):
    runtime = {
        "started": True,
        "ready": True,
        "kill_switch_active": False,
        "trading_enabled": True,
        "dry_run": False,
        "open_orders": 0,
    }
    runtime.update(runtime_overrides)
    return {
        "runtime": runtime,
        "recovery": {
            "fill_checkpoint_enabled": True,
            "fill_accounting_enabled": True,
            "position_recovery_enabled": True,
            "lifecycle_enabled": True,
        },
    }


go = PaperReadiness(SimpleNamespace(), Diagnostics(snapshot())).assess()
assert go.ready is True
assert go.blockers == ()

safe_default = PaperReadiness(
    SimpleNamespace(),
    Diagnostics(snapshot(trading_enabled=False, dry_run=True)),
).assess()
assert safe_default.ready is False
assert "trading_enabled" in safe_default.blockers
assert "dry_run_disabled" in safe_default.blockers

kill_switch = PaperReadiness(
    SimpleNamespace(),
    Diagnostics(snapshot(kill_switch_active=True)),
).assess()
assert kill_switch.ready is False
assert "kill_switch_clear" in kill_switch.blockers

open_order = PaperReadiness(
    SimpleNamespace(),
    Diagnostics(snapshot(open_orders=1)),
).assess()
assert open_order.ready is False
assert "no_open_orders" in open_order.blockers

print("=== TRADING APP v2.0 / PAPER READINESS ===")
print("Fully satisfied readiness returns GO: PASS")
print("Safe default returns NO-GO: PASS")
print("Kill switch returns NO-GO: PASS")
print("Outstanding order returns NO-GO: PASS")
print("Read-only broker interaction: NONE")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
