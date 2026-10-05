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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS order_idempotency (
                    key TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS managed_orders (
                    order_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    reason TEXT
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


    def reserve_order_key(self, key: str) -> bool:
        normalized = key.strip()
        if not normalized:
            raise ValueError("Idempotency key is required.")
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO order_idempotency(key) VALUES (?)",
                    (normalized,),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def has_order_key(self, key: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM order_idempotency WHERE key = ?",
                (key.strip(),),
            ).fetchone()
        return row is not None


    def save_managed_order(self, order) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO managed_orders(order_id, state, reason)
                VALUES (?, ?, ?)
                ON CONFLICT(order_id) DO UPDATE SET
                    state=excluded.state,
                    reason=excluded.reason
                """,
                (order.order_id, order.state.value, order.reason),
            )

    def load_managed_order(self, order_id: str):
        from app.trading.order_state import ManagedOrder, OrderState

        with self._connect() as connection:
            row = connection.execute(
                "SELECT order_id, state, reason FROM managed_orders WHERE order_id = ?",
                (order_id,),
            ).fetchone()
        if row is None:
            return None
        return ManagedOrder(
            order_id=row["order_id"],
            state=OrderState(row["state"]),
            reason=row["reason"],
        )


    def create_order_atomically(self, order, idempotency_key: str) -> bool:
        """Create lifecycle and idempotency records in one SQLite transaction."""
        normalized = idempotency_key.strip()
        if not normalized:
            raise ValueError("Idempotency key is required.")
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "INSERT INTO order_idempotency(key) VALUES (?)",
                    (normalized,),
                )
                connection.execute(
                    """
                    INSERT INTO managed_orders(order_id, state, reason)
                    VALUES (?, ?, ?)
                    """,
                    (order.order_id, order.state.value, order.reason),
                )
            return True
        except sqlite3.IntegrityError:
            return False
