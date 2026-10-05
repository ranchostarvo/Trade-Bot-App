import json
import os
import sqlite3
from pathlib import Path

from app.audit import AuditEvent
from app.trading.order_state import ManagedOrder, OrderState


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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS order_recovery_context (
                    order_id TEXT PRIMARY KEY,
                    bot_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity TEXT NOT NULL,
                    estimated_price TEXT NOT NULL,
                    broker_order_id TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS capital_reservations (
                    bot_id TEXT PRIMARY KEY,
                    amount TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS exposure_reservations (
                    bot_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    notional TEXT NOT NULL,
                    PRIMARY KEY(bot_id, symbol)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS order_settlements (
                    order_id TEXT PRIMARY KEY,
                    outcome TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_exposure (
                    order_id TEXT PRIMARY KEY,
                    bot_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    notional TEXT NOT NULL
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


    def reserve_capital_atomically(self, bot_id: str, amount, account_cash) -> bool:
        from decimal import Decimal

        bot_id = bot_id.strip()
        amount = Decimal(str(amount))
        account_cash = Decimal(str(account_cash))
        if not bot_id or amount <= 0 or account_cash < 0:
            raise ValueError("Invalid capital reservation.")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                "SELECT amount FROM capital_reservations"
            ).fetchall()
            reserved = sum(
                (Decimal(row["amount"]) for row in rows), Decimal("0")
            )
            if reserved + amount > account_cash:
                return False
            try:
                connection.execute(
                    "INSERT INTO capital_reservations(bot_id, amount) VALUES (?, ?)",
                    (bot_id, str(amount)),
                )
            except sqlite3.IntegrityError:
                return False
        return True

    def load_capital_reservations(self) -> dict[str, str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT bot_id, amount FROM capital_reservations"
            ).fetchall()
        return {row["bot_id"]: row["amount"] for row in rows}


    def reserve_exposure_atomically(
        self, bot_id: str, symbol: str, notional, account_equity,
        max_symbol_notional, max_symbol_pct
    ) -> bool:
        from decimal import Decimal

        bot_id = bot_id.strip()
        symbol = symbol.strip().upper()
        notional = Decimal(str(notional))
        equity = Decimal(str(account_equity))
        max_notional = Decimal(str(max_symbol_notional))
        max_pct = Decimal(str(max_symbol_pct))
        if not bot_id or not symbol or notional <= 0 or equity <= 0:
            raise ValueError("Invalid exposure reservation.")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                "SELECT notional FROM exposure_reservations WHERE symbol = ?",
                (symbol,),
            ).fetchall()
            current = sum(
                (Decimal(row["notional"]) for row in rows), Decimal("0")
            )
            proposed = current + notional
            pct = (proposed / equity) * Decimal("100")
            if proposed > max_notional or pct > max_pct:
                return False
            try:
                connection.execute(
                    """
                    INSERT INTO exposure_reservations(bot_id, symbol, notional)
                    VALUES (?, ?, ?)
                    """,
                    (bot_id, symbol, str(notional)),
                )
            except sqlite3.IntegrityError:
                return False
        return True

    def load_exposure_reservations(self, symbol: str) -> dict[str, str]:
        symbol = symbol.strip().upper()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT bot_id, notional FROM exposure_reservations
                WHERE symbol = ?
                """,
                (symbol,),
            ).fetchall()
        return {row["bot_id"]: row["notional"] for row in rows}


    def release_capital_atomically(self, bot_id: str) -> bool:
        bot_id = bot_id.strip()
        if not bot_id:
            raise ValueError("bot_id is required.")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                "DELETE FROM capital_reservations WHERE bot_id = ?",
                (bot_id,),
            )
        return cursor.rowcount == 1


    def release_exposure_atomically(
        self, bot_id: str, symbol: str, notional=None
    ) -> bool:
        from decimal import Decimal

        bot_id = bot_id.strip()
        symbol = symbol.strip().upper()
        if not bot_id or not symbol:
            raise ValueError("bot_id and symbol are required.")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT notional FROM exposure_reservations
                WHERE bot_id = ? AND symbol = ?
                """,
                (bot_id, symbol),
            ).fetchone()
            if row is None:
                return False
            held = Decimal(row["notional"])
            release = held if notional is None else Decimal(str(notional))
            if release <= 0 or release > held:
                raise ValueError("Invalid exposure release amount.")
            remaining = held - release
            if remaining == 0:
                connection.execute(
                    """
                    DELETE FROM exposure_reservations
                    WHERE bot_id = ? AND symbol = ?
                    """,
                    (bot_id, symbol),
                )
            else:
                connection.execute(
                    """
                    UPDATE exposure_reservations SET notional = ?
                    WHERE bot_id = ? AND symbol = ?
                    """,
                    (str(remaining), bot_id, symbol),
                )
        return True


    def reserve_pending_exposure(self, order_id, bot_id, symbol, notional) -> bool:
        order_id = order_id.strip()
        bot_id = bot_id.strip()
        symbol = symbol.strip().upper()
        if not order_id or not bot_id or not symbol:
            raise ValueError("order_id, bot_id and symbol are required.")
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO pending_exposure(order_id, bot_id, symbol, notional)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, bot_id, symbol, str(notional)),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def release_pending_exposure(self, order_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM pending_exposure WHERE order_id = ?",
                (order_id.strip(),),
            )
        return cursor.rowcount == 1

    def load_pending_exposure(self) -> dict[str, dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT order_id, bot_id, symbol, notional FROM pending_exposure"
            ).fetchall()
        return {
            row["order_id"]: {
                "bot_id": row["bot_id"],
                "symbol": row["symbol"],
                "notional": row["notional"],
            }
            for row in rows
        }


    def reserve_pending_exposure_with_limits(
        self, order_id, bot_id, symbol, notional, account_equity,
        max_symbol_notional, max_symbol_pct
    ) -> bool:
        from decimal import Decimal

        order_id = order_id.strip()
        bot_id = bot_id.strip()
        symbol = symbol.strip().upper()
        proposed_add = Decimal(str(notional))
        equity = Decimal(str(account_equity))
        max_notional = Decimal(str(max_symbol_notional))
        max_pct = Decimal(str(max_symbol_pct))
        if (
            not order_id or not bot_id or not symbol
            or proposed_add <= 0 or equity <= 0
        ):
            raise ValueError("Invalid pending exposure reservation.")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            filled_rows = connection.execute(
                "SELECT notional FROM exposure_reservations WHERE symbol = ?",
                (symbol,),
            ).fetchall()
            pending_rows = connection.execute(
                "SELECT notional FROM pending_exposure WHERE symbol = ?",
                (symbol,),
            ).fetchall()
            committed = sum(
                (Decimal(row["notional"]) for row in filled_rows),
                Decimal("0"),
            ) + sum(
                (Decimal(row["notional"]) for row in pending_rows),
                Decimal("0"),
            )
            proposed = committed + proposed_add
            pct = (proposed / equity) * Decimal("100")
            if proposed > max_notional or pct > max_pct:
                return False
            try:
                connection.execute(
                    """
                    INSERT INTO pending_exposure(order_id, bot_id, symbol, notional)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, bot_id, symbol, str(proposed_add)),
                )
            except sqlite3.IntegrityError:
                return False
        return True


    def settle_pending_buy_atomically(self, order_id: str) -> bool:
        from decimal import Decimal

        order_id = order_id.strip()
        if not order_id:
            raise ValueError("order_id is required.")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT bot_id, symbol, notional
                FROM pending_exposure
                WHERE order_id = ?
                """,
                (order_id,),
            ).fetchone()
            if row is None:
                return False

            existing = connection.execute(
                """
                SELECT notional FROM exposure_reservations
                WHERE bot_id = ? AND symbol = ?
                """,
                (row["bot_id"], row["symbol"]),
            ).fetchone()
            filled = Decimal(existing["notional"]) if existing else Decimal("0")
            new_total = filled + Decimal(row["notional"])
            connection.execute(
                """
                INSERT INTO exposure_reservations(bot_id, symbol, notional)
                VALUES (?, ?, ?)
                ON CONFLICT(bot_id, symbol)
                DO UPDATE SET notional = excluded.notional
                """,
                (row["bot_id"], row["symbol"], str(new_total)),
            )
            connection.execute(
                "DELETE FROM pending_exposure WHERE order_id = ?",
                (order_id,),
            )
        return True


    def load_unresolved_orders(self):
        placeholders = ", ".join("?" for _ in ("SUBMITTED", "ACKNOWLEDGED"))
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT order_id, state, reason
                FROM managed_orders
                WHERE state IN ({placeholders})
                ORDER BY order_id
                """,
                ("SUBMITTED", "ACKNOWLEDGED"),
            ).fetchall()
        orders = []
        for row in rows:
            order = ManagedOrder(row["order_id"])
            order.state = OrderState(row["state"])
            order.rejection_reason = row["reason"]
            orders.append(order)
        return orders


    def save_order_recovery_context(
        self, order_id, bot_id, symbol, side, quantity, estimated_price,
        broker_order_id=None,
    ):
        values = [
            str(value).strip()
            for value in (order_id, bot_id, symbol, side, quantity, estimated_price)
        ]
        if not all(values):
            raise ValueError("Complete order recovery context is required.")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO order_recovery_context(
                    order_id, bot_id, symbol, side, quantity,
                    estimated_price, broker_order_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(order_id) DO UPDATE SET
                    bot_id=excluded.bot_id,
                    symbol=excluded.symbol,
                    side=excluded.side,
                    quantity=excluded.quantity,
                    estimated_price=excluded.estimated_price,
                    broker_order_id=excluded.broker_order_id
                """,
                (*values, broker_order_id),
            )

    def load_order_recovery_context(self, order_id):
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT order_id, bot_id, symbol, side, quantity,
                       estimated_price, broker_order_id
                FROM order_recovery_context
                WHERE order_id = ?
                """,
                (order_id,),
            ).fetchone()
        return dict(row) if row is not None else None


    def claim_order_settlement(self, order_id: str, outcome: str) -> bool:
        order_id = order_id.strip()
        outcome = outcome.strip().upper()
        if not order_id or not outcome:
            raise ValueError("order_id and outcome are required.")
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO order_settlements(order_id, outcome)
                    VALUES (?, ?)
                    """,
                    (order_id, outcome),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def load_order_settlement(self, order_id: str):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT outcome FROM order_settlements WHERE order_id = ?",
                (order_id,),
            ).fetchone()
        return row["outcome"] if row is not None else None
