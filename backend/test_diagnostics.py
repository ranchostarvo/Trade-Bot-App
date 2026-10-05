from decimal import Decimal
from types import SimpleNamespace

from app.trading.diagnostics import RuntimeDiagnostics
from app.trading.runtime import RuntimeStatus


class Runtime:
    def __init__(self):
        self.recovery_manager = SimpleNamespace(
            fill_checkpoint_store=object(),
            fill_accounting=object(),
        )
        self.position_recovery_manager = object()
        self.lifecycle_service = object()
        self.execution_engine = SimpleNamespace(
            risk=SimpleNamespace(
                config=SimpleNamespace(
                    max_order_notional=Decimal("500"),
                    max_daily_loss_pct=Decimal("2.5"),
                )
            )
        )

    def status(self):
        return RuntimeStatus(
            started=True,
            ready=True,
            kill_switch_active=False,
            kill_switch_reason="",
            trading_enabled=False,
            dry_run=True,
            open_orders=0,
        )


snapshot = RuntimeDiagnostics(Runtime()).snapshot()
assert snapshot["runtime"]["ready"] is True
assert snapshot["runtime"]["trading_enabled"] is False
assert snapshot["runtime"]["dry_run"] is True
assert snapshot["risk_limits"]["max_order_notional"] == "500"
assert snapshot["risk_limits"]["max_daily_loss_pct"] == "2.5"
assert "credentials" not in snapshot
assert "api_key" not in str(snapshot).lower()
assert "secret" not in str(snapshot).lower()
assert snapshot["recovery"]["fill_checkpoint_enabled"] is True
assert snapshot["recovery"]["fill_accounting_enabled"] is True
assert snapshot["recovery"]["position_recovery_enabled"] is True
assert snapshot["recovery"]["lifecycle_enabled"] is True

print("=== TRADING APP v2.0 / DIAGNOSTICS ===")
print("Runtime status exposed: PASS")
print("Risk ceilings exposed: PASS")
print("Trading-disabled state exposed: PASS")
print("Credentials excluded: PASS")
print("Recovery readiness exposed: PASS")
print("Lifecycle readiness exposed: PASS")
print("Broker interaction: NO")
print("RESULT: PASS")
