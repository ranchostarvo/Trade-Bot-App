from app.trading.readiness import ReadinessReport
from app.trading.readiness_summary import PaperReadinessSummary


summary = PaperReadinessSummary()

go = summary.render(ReadinessReport(
    ready=True,
    checks={"runtime_ready": True},
    blockers=(),
))
assert go["decision"] == "GO"
assert go["ready"] is True
assert go["blocker_count"] == 0
assert go["blockers"] == []

no_go = summary.render(ReadinessReport(
    ready=False,
    checks={
        "trading_enabled": False,
        "dry_run_disabled": False,
        "kill_switch_clear": False,
        "no_open_orders": False,
    },
    blockers=(
        "trading_enabled",
        "dry_run_disabled",
        "kill_switch_clear",
        "no_open_orders",
    ),
))
assert no_go["decision"] == "NO-GO"
assert no_go["ready"] is False
assert no_go["blocker_count"] == 4
assert "Paper order transmission is disabled." in no_go["blockers"]
assert "Runtime is still in dry-run mode." in no_go["blockers"]
assert "Global kill switch is active." in no_go["blockers"]
assert "An outstanding order must be reconciled first." in no_go["blockers"]

unknown = summary.render(ReadinessReport(
    ready=False,
    checks={"future_check": False},
    blockers=("future_check",),
))
assert unknown["blockers"] == ["future_check"]

print("=== TRADING APP v2.0 / READINESS SUMMARY ===")
print("GO rendering: PASS")
print("NO-GO rendering: PASS")
print("Plain-English blockers: PASS")
print("Forward-compatible unknown blocker: PASS")
print("Broker interaction: NONE")
print("Real Alpaca order submitted: NO")
print("RESULT: PASS")
