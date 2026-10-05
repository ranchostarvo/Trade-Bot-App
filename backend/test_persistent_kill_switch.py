import tempfile
from pathlib import Path

from app.trading.kill_switch import (
    KillSwitch,
    KillSwitchActive,
)
from app.trading.risk_store import RiskStateStore


print(
    "=== TRADING APP v2.0 / "
    "PERSISTENT KILL SWITCH ==="
)

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "risk_state.json"

    store = RiskStateStore(path)

    kill_switch = KillSwitch(store=store)

    assert kill_switch.active is False
    print("Initial switch inactive: PASS")

    kill_switch.engage(
        "Emergency shutdown test"
    )

    assert kill_switch.active is True
    print("Kill switch engaged: PASS")

    # Simulate complete application restart.
    restarted_store = RiskStateStore(path)
    restarted_switch = KillSwitch(
        store=restarted_store
    )

    assert restarted_switch.active is True
    assert restarted_switch.reason == (
        "Emergency shutdown test"
    )

    print(
        "Engaged state survives restart: PASS"
    )

    try:
        restarted_switch.validate()
        raise AssertionError(
            "Restarted kill switch failed open."
        )
    except KillSwitchActive:
        print(
            "Restarted switch blocks trading: PASS"
        )

    restarted_switch.reset()

    second_restart = KillSwitch(
        store=RiskStateStore(path)
    )

    assert second_restart.active is False

    print(
        "Reset survives second restart: PASS"
    )

    # Deliberately corrupt persisted safety state.
    path.write_text(
        "{corrupt",
        encoding="utf-8",
    )

    corrupted_restart = KillSwitch(
        store=RiskStateStore(path)
    )

    assert corrupted_restart.active is True

    try:
        corrupted_restart.validate()
        raise AssertionError(
            "Corrupt state failed open."
        )
    except KillSwitchActive:
        print(
            "Corrupt persisted state blocks trading: PASS"
        )

print("No broker order submitted: PASS")
print("RESULT: PASS")
