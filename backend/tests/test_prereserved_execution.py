from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.execution import ExecutionEngine
from app.trading.idempotency import PersistentIdempotencyRegistry
from app.trading.risk import OrderRequest


def buy():
    return OrderRequest(
        symbol="SPY",
        side="buy",
        quantity=Decimal("1"),
        estimated_price=Decimal("100"),
    )


def test_pre_reserved_execution_requires_real_reservation(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    execution = ExecutionEngine(
        idempotency_registry=PersistentIdempotencyRegistry(store)
    )
    try:
        execution.execute(
            buy(),
            idempotency_key="missing",
            idempotency_reserved=True,
        )
    except RuntimeError as exc:
        assert "reservation does not exist" in str(exc)
        return
    raise AssertionError("Execution trusted a nonexistent reservation.")


def test_pre_reserved_execution_preserves_registry_dependency(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    registry = PersistentIdempotencyRegistry(store)
    registry.reserve("existing")
    execution = ExecutionEngine(idempotency_registry=registry)

    result = execution.execute(
        buy(),
        idempotency_key="existing",
        idempotency_reserved=True,
    )
    assert result["status"] == "DRY_RUN"
    assert execution.idempotency_registry is registry
