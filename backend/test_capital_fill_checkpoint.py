import tempfile
from decimal import Decimal
from pathlib import Path

from app.trading.capital_fill_checkpoint import CapitalFillCheckpointStore
from app.trading.risk import RiskRejected

with tempfile.TemporaryDirectory() as root:
    store = CapitalFillCheckpointStore(Path(root) / "fills.json")
    dq, dv = store.delta("order-1", Decimal("0.4"), Decimal("200"))
    assert dq == Decimal("0.4") and dv == Decimal("200")
    store.commit("order-1", Decimal("0.4"), Decimal("200"))

    dq, dv = store.delta("order-1", Decimal("1.0"), Decimal("510"))
    assert dq == Decimal("0.6") and dv == Decimal("310")
    store.commit("order-1", Decimal("1.0"), Decimal("510"))

    assert store.delta("order-1", Decimal("1.0"), Decimal("510")) == (
        Decimal("0"), Decimal("0")
    )
    try:
        store.delta("order-1", Decimal("0.9"), Decimal("500"))
        raise AssertionError("Regression must fail closed.")
    except RiskRejected:
        pass

print("CAPITAL FILL CHECKPOINT: PASS")
print("Partial fill delta: PASS")
print("Average-price cumulative value delta: PASS")
print("Replay idempotency: PASS")
print("Regression fail closed: PASS")
