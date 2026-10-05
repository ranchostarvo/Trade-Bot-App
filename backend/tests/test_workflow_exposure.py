from decimal import Decimal

import pytest

from app.storage import SQLiteStore
from app.trading.execution import ExecutionEngine
from app.trading.idempotency import PersistentIdempotencyRegistry
from app.trading.resources import DurableResourceCoordinator
from app.trading.risk import OrderRequest, RiskConfig, RiskEngine
from app.trading.workflow import DurableExecutionWorkflow


def setup(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    resources = DurableResourceCoordinator(
        store, Decimal("50000"), Decimal("100000")
    )
    execution = ExecutionEngine(
        idempotency_registry=PersistentIdempotencyRegistry(store)
    )
    return store, resources, DurableExecutionWorkflow(
        execution, store, resources
    )


def buy(notional="100"):
    price = Decimal("100")
    return OrderRequest(
        "SPY", "buy", Decimal(notional) / price, price
    )


def test_buy_workflow_reserves_durable_exposure(tmp_path):
    store, resources, flow = setup(tmp_path)
    result = flow.process("order-1", buy(), bot_id="bot-1")
    assert result["order_state"] == "RESERVED"
    assert store.load_pending_exposure() == {
        "order-1": {"bot_id": "bot-1", "symbol": "SPY", "notional": "100"}
    }


def test_failed_execution_releases_exposure(tmp_path):
    store, resources, flow = setup(tmp_path)
    flow.execution.risk = RiskEngine(
        RiskConfig(dry_run=False, trading_enabled=True)
    )

    with pytest.raises(RuntimeError, match="intentionally not implemented"):
        flow.process("order-1", buy(), bot_id="bot-1")

    assert store.load_pending_exposure() == {}


def test_resources_require_bot_identity(tmp_path):
    _, _, flow = setup(tmp_path)
    with pytest.raises(ValueError, match="bot_id is required"):
        flow.process("order-1", buy())
