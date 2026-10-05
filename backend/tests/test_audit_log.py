from app.audit import AuditLog


def test_audit_log_builds_valid_hash_chain():
    log = AuditLog()
    first = log.record("BOT_START", "SUCCESS", "bot-1")
    second = log.record("BOT_STOP", "SUCCESS", "bot-1")
    assert first.sequence == 1
    assert second.sequence == 2
    assert second.previous_hash == first.event_hash
    assert log.verify() is True


def test_audit_events_are_append_only_view():
    log = AuditLog()
    log.record("EMERGENCY_STOP", "SUCCESS", "fleet", "test")
    events = log.events()
    assert isinstance(events, tuple)
    assert len(events) == 1
