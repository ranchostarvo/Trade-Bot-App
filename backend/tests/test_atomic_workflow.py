from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.execution import ExecutionEngine
from app.trading.idempotency import DuplicateOrder, PersistentIdempotencyRegistry
from app.trading.risk import OrderRequest
from app.trading.workflow import DurableExecutionWorkflow


def buy():
    return OrderRequest(
        symbol="SPY",
        side="buy",
        quantity=Decimal("1"),
        estimated_price=Decimal("100"),
    )


def test_workflow_atomically_reserves_order_identity(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    execution = ExecutionEngine(
        idempotency_registry=PersistentIdempotencyRegistry(store)
    )
    flow = DurableExecutionWorkflow(execution, store)

    result = flow.process("atomic-order", buy())
    assert result["order_state"] == "RESERVED"
    assert store.has_order_key("atomic-order") is True

    try:
        flow.process("atomic-order", buy())
    except DuplicateOrder:
        return
    raise AssertionError("Atomic workflow accepted duplicate order.")
