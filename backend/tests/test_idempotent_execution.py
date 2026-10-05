from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.execution import ExecutionEngine
from app.trading.idempotency import (
    DuplicateOrder,
    PersistentIdempotencyRegistry,
)
from app.trading.risk import OrderRequest


def buy():
    return OrderRequest(
        symbol="SPY",
        side="buy",
        quantity=Decimal("1"),
        estimated_price=Decimal("100"),
    )


def engine(tmp_path):
    registry = PersistentIdempotencyRegistry(
        SQLiteStore(str(tmp_path / "trading.db"))
    )
    return ExecutionEngine(idempotency_registry=registry)


def test_protected_execution_requires_idempotency_key(tmp_path):
    try:
        engine(tmp_path).execute(buy())
    except RuntimeError as exc:
        assert "Idempotency key is required" in str(exc)
        return
    raise AssertionError("Protected execution accepted a missing key.")


def test_first_key_executes_dry_run_and_duplicate_is_rejected(tmp_path):
    execution = engine(tmp_path)
    result = execution.execute(buy(), idempotency_key="order-001")
    assert result["status"] == "DRY_RUN"
    assert result["submitted"] is False
    assert result["idempotency_key"] == "order-001"

    try:
        execution.execute(buy(), idempotency_key="order-001")
    except DuplicateOrder:
        return
    raise AssertionError("Duplicate order reached execution twice.")


def test_duplicate_remains_rejected_after_engine_restart(tmp_path):
    path = tmp_path / "trading.db"
    first = ExecutionEngine(
        idempotency_registry=PersistentIdempotencyRegistry(
            SQLiteStore(str(path))
        )
    )
    first.execute(buy(), idempotency_key="restart-order")

    restarted = ExecutionEngine(
        idempotency_registry=PersistentIdempotencyRegistry(
            SQLiteStore(str(path))
        )
    )
    try:
        restarted.execute(buy(), idempotency_key="restart-order")
    except DuplicateOrder:
        return
    raise AssertionError("Restart allowed duplicate order execution.")
