from dataclasses import dataclass
from threading import Lock


class DuplicateOrder(RuntimeError):
    """Raised when the same logical order is attempted more than once."""


@dataclass(frozen=True)
class OrderIntent:
    idempotency_key: str


class IdempotencyRegistry:
    """Process-local atomic reservation of logical order identifiers."""

    def __init__(self):
        self._keys = set()
        self._lock = Lock()

    def reserve(self, key: str) -> None:
        normalized = key.strip()
        if not normalized:
            raise ValueError("Idempotency key is required.")
        with self._lock:
            if normalized in self._keys:
                raise DuplicateOrder(
                    f"Order intent {normalized} has already been processed."
                )
            self._keys.add(normalized)

    def contains(self, key: str) -> bool:
        with self._lock:
            return key.strip() in self._keys


class PersistentIdempotencyRegistry:
    """Durable atomic duplicate-order protection backed by SQLiteStore."""

    def __init__(self, store):
        self.store = store

    def reserve(self, key: str) -> None:
        normalized = key.strip()
        if not normalized:
            raise ValueError("Idempotency key is required.")
        if not self.store.reserve_order_key(normalized):
            raise DuplicateOrder(
                f"Order intent {normalized} has already been processed."
            )

    def contains(self, key: str) -> bool:
        return self.store.has_order_key(key)
