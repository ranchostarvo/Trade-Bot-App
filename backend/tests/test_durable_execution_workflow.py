from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.execution import ExecutionEngine
from app.trading.idempotency import DuplicateOrder, PersistentIdempotencyRegistry
from app.trading.order_state import OrderState
from app.trading.risk import OrderRequest, RiskRejected
from app.trading.workflow import DurableExecutionWorkflow


def buy(price="100"):
    return OrderRequest(
        symbol="SPY",
        side="buy",
        quantity=Decimal("1"),
        estimated_price=Decimal(price),
    )


def workflow(path):
    store = SQLiteStore(str(path))
    execution = ExecutionEngine(
        idempotency_registry=PersistentIdempotencyRegistry(store)
    )
    return DurableExecutionWorkflow(execution, store), store


def test_workflow_persists_reserved_dry_run(tmp_path):
    flow, store = workflow(tmp_path / "trading.db")
    result = flow.process("order-1", buy())
    assert result["status"] == "DRY_RUN"
    assert result["order_state"] == "RESERVED"
    assert store.load_managed_order("order-1").state == OrderState.RESERVED


def test_workflow_rejects_existing_order_after_restart(tmp_path):
    path = tmp_path / "trading.db"
    first, _ = workflow(path)
    first.process("order-1", buy())

    restarted, _ = workflow(path)
    try:
        restarted.process("order-1", buy())
    except DuplicateOrder:
        return
    raise AssertionError("Restart treated existing order as new.")


def test_risk_failure_is_persisted_as_rejected(tmp_path):
    flow, store = workflow(tmp_path / "trading.db")
    try:
        flow.process("order-risk", buy("600"))
    except RiskRejected:
        recovered = store.load_managed_order("order-risk")
        assert recovered.state == OrderState.REJECTED
        assert recovered.reason
        return
    raise AssertionError("Risk violation was accepted.")
