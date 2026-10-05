from app.audit import AuditLog
from app.storage import SQLiteStore


def test_audit_survives_restart(tmp_path):
    path = tmp_path / "trading.db"
    store = SQLiteStore(str(path))
    log = AuditLog(store)
    log.record("BOT_START", "SUCCESS", "bot-1")

    restarted = AuditLog(SQLiteStore(str(path)))
    assert len(restarted.events()) == 1
    assert restarted.events()[0].action == "BOT_START"
    assert restarted.verify() is True


def test_application_state_survives_restart(tmp_path):
    path = tmp_path / "trading.db"
    store = SQLiteStore(str(path))
    store.set_state("kill_switch", {"engaged": True, "reason": "test"})

    restarted = SQLiteStore(str(path))
    state = restarted.get_state("kill_switch")
    assert state["engaged"] is True
    assert state["reason"] == "test"
