from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.execution import ExecutionEngine
from app.trading.idempotency import PersistentIdempotencyRegistry
from app.trading.resources import DurableResourceCoordinator
from app.trading.risk import OrderRequest
from app.trading.workflow import DurableExecutionWorkflow


class Account:
    account_blocked = False
    trading_blocked = False


class Positions:
    def quantity(self, symbol):
        return Decimal("10")


class Reconciler:
    def reconcile(self):
        return Account(), Positions()


def test_sell_reduces_existing_durable_exposure(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    resources = DurableResourceCoordinator(
        store, Decimal("50000"), Decimal("100000")
    )
    resources.reserve_symbol_exposure("bot-1", "SPY", Decimal("500"))

    execution = ExecutionEngine(
        reconciler=Reconciler(),
        idempotency_registry=PersistentIdempotencyRegistry(store),
    )
    flow = DurableExecutionWorkflow(execution, store, resources)
    sell = OrderRequest(
        "SPY", "sell", Decimal("2"), Decimal("100")
    )

    result = flow.process("sell-1", sell, bot_id="bot-1")

    assert result["status"] == "DRY_RUN"
    assert result["exposure_released"] is False
    assert store.load_exposure_reservations("SPY") == {"bot-1": "500"}
