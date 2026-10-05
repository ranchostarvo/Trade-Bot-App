from types import SimpleNamespace

from app.trading.kill_switch import KillSwitch
from app.trading.startup import StartupGate


class ClearRecovery:
    def reconcile(self):
        return []


class BlockingRecovery:
    def __init__(self, kill_switch):
        self.kill_switch = kill_switch

    def reconcile(self):
        self.kill_switch.engage("unresolved broker orders")
        raise RuntimeError("blocked")


def runtime(recovery):
    return SimpleNamespace(
        kill_switch=KillSwitch(),
        restart_recovery=recovery,
    )


def test_startup_ready_only_after_clean_recovery():
    rt = runtime(ClearRecovery())
    status = StartupGate(rt).evaluate()
    assert status.ready is True
    assert status.kill_switch_engaged is False


def test_startup_blocks_when_recovery_is_unavailable():
    rt = runtime(None)
    status = StartupGate(rt).evaluate()
    assert status.ready is False
    assert rt.kill_switch.engaged is True


def test_startup_preserves_recovery_kill_switch():
    switch = KillSwitch()
    rt = SimpleNamespace(
        kill_switch=switch,
        restart_recovery=BlockingRecovery(switch),
    )
    status = StartupGate(rt).evaluate()
    assert status.ready is False
    assert status.reason == "unresolved broker orders"
    assert switch.engaged is True
