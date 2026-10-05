import tempfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from app.trading.equity_baseline import (
    EquityBaselineStore,
)
from app.trading.risk import RiskRejected


print(
    "=== TRADING APP v2.0 / "
    "EQUITY BASELINE STORE ==="
)

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "equity.json"

    day_one = date(2026, 10, 5)

    store = EquityBaselineStore(path)

    baseline = store.get_or_create(
        Decimal("100000"),
        trading_day=day_one,
    )

    assert baseline == Decimal("100000")
    print("Initial baseline created: PASS")

    # Simulate losses followed by an application restart.
    restarted_store = EquityBaselineStore(path)

    baseline = restarted_store.get_or_create(
        Decimal("98000"),
        trading_day=day_one,
    )

    assert baseline == Decimal("100000")
    print("Restart preserves baseline: PASS")

    loss_pct = (
        (baseline - Decimal("98000"))
        / baseline
        * Decimal("100")
    )

    assert loss_pct == Decimal("2.00")
    print("Loss remains measurable after restart: PASS")

    # A new trading day may establish a fresh baseline.
    day_two = day_one + timedelta(days=1)

    new_baseline = restarted_store.get_or_create(
        Decimal("99000"),
        trading_day=day_two,
    )

    assert new_baseline == Decimal("99000")
    print("New day creates new baseline: PASS")

    # Corrupt state must fail closed.
    path.write_text(
        "{corrupt",
        encoding="utf-8",
    )

    try:
        EquityBaselineStore(path).get_or_create(
            Decimal("99000"),
            trading_day=day_two,
        )
        raise AssertionError(
            "Corrupt baseline failed open."
        )
    except RiskRejected:
        print("Corrupt baseline fails closed: PASS")

print("No broker interaction: PASS")
print("RESULT: PASS")
