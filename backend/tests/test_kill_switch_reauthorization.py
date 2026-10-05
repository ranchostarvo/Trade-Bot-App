from app.trading.kill_switch import KillSwitch


def test_kill_switch_requires_exact_confirmation():
    switch = KillSwitch()
    switch.engage("test")
    try:
        switch.reset("yes")
    except RuntimeError:
        assert switch.engaged is True
        return
    raise AssertionError("Kill switch cleared without exact confirmation.")


def test_kill_switch_can_be_explicitly_cleared():
    switch = KillSwitch()
    switch.engage("test")
    switch.reset("CLEAR-KILL-SWITCH")
    assert switch.engaged is False
    assert switch.reason is None


def test_clear_when_not_engaged_is_rejected():
    switch = KillSwitch()
    try:
        switch.reset("CLEAR-KILL-SWITCH")
    except RuntimeError:
        return
    raise AssertionError("Inactive kill switch accepted a reset.")
