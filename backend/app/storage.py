import json
import os
import sqlite3
from pathlib import Path

from app.audit import AuditEvent


class SQLiteStore:
    """Durable local state for audit events and application metadata."""

    def __init__(self, path: str | None = None):
        db_path = path or os.getenv("TRADING_DB_PATH", "data/trading_app.db")
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    sequence INTEGER PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

    def append_audit(self, event: AuditEvent) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_events (
                    sequence, timestamp, action, outcome, subject, detail,
                    previous_hash, event_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.sequence,
                    event.timestamp,
                    event.action,
                    event.outcome,
                    event.subject,
                    event.detail,
                    event.previous_hash,
                    event.event_hash,
                ),
            )

    def load_audit(self) -> list[AuditEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM audit_events ORDER BY sequence"
            ).fetchall()
        return [AuditEvent(**dict(row)) for row in rows]

    def set_state(self, key: str, value) -> None:
        encoded = json.dumps(value, sort_keys=True)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO app_state(key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (key, encoded),
            )

    def get_state(self, key: str, default=None):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_state WHERE key = ?", (key,)
            ).fetchone()
        return default if row is None else json.loads(row["value"])
