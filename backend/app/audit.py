from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    timestamp: str
    action: str
    outcome: str
    subject: str
    detail: str
    previous_hash: str
    event_hash: str


class AuditLog:
    """In-memory hash-chained audit log. Persistent storage comes later."""

    def __init__(self):
        self._events: list[AuditEvent] = []

    def record(
        self,
        action: str,
        outcome: str,
        subject: str = "",
        detail: str = "",
    ) -> AuditEvent:
        previous_hash = self._events[-1].event_hash if self._events else ""
        sequence = len(self._events) + 1
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = {
            "sequence": sequence,
            "timestamp": timestamp,
            "action": action,
            "outcome": outcome,
            "subject": subject,
            "detail": detail,
            "previous_hash": previous_hash,
        }
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        ).encode()
        event_hash = hashlib.sha256(encoded).hexdigest()
        event = AuditEvent(**payload, event_hash=event_hash)
        self._events.append(event)
        return event

    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def verify(self) -> bool:
        previous_hash = ""
        for event in self._events:
            payload = asdict(event)
            event_hash = payload.pop("event_hash")
            if payload["previous_hash"] != previous_hash:
                return False
            encoded = json.dumps(
                payload, sort_keys=True, separators=(",", ":")
            ).encode()
            if hashlib.sha256(encoded).hexdigest() != event_hash:
                return False
            previous_hash = event_hash
        return True
