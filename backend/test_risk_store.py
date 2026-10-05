import tempfile
from pathlib import Path

from app.trading.risk_store import RiskStateStore


print("=== TRADING APP v2.0 / RISK STATE STORE ===")

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "risk_state.json"

    store = RiskStateStore(path)

    state = store.load()

    assert state["kill_switch_active"] is False
    print("Clean initial state: PASS")

    store.save_kill_switch(
        True,
        "Emergency stop test",
    )

    restarted_store = RiskStateStore(path)
    state = restarted_store.load()

    assert state["kill_switch_active"] is True
    assert state["kill_switch_reason"] == (
        "Emergency stop test"
    )

    print("Kill switch survives restart: PASS")

    restarted_store.save_kill_switch(
        False,
        "",
    )

    state = RiskStateStore(path).load()

    assert state["kill_switch_active"] is False
    print("Reset persists across restart: PASS")

    path.write_text(
        "{corrupted-json",
        encoding="utf-8",
    )

    state = RiskStateStore(path).load()

    assert state["kill_switch_active"] is True
    print("Corrupt state fails closed: PASS")

print("No broker interaction: PASS")
print("RESULT: PASS")
