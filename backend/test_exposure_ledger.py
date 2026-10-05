import tempfile
from pathlib import Path
from decimal import Decimal

from app.trading.exposure_ledger import PortfolioExposureLedger
from app.trading.risk import RiskRejected

with tempfile.TemporaryDirectory() as root:
    path = Path(root) / "exposure.json"
    ledger = PortfolioExposureLedger(path, Decimal("50000"))
    for i in range(100):
        ledger.allocate(f"bot-{i:03d}", Decimal("500"))
    assert ledger.total_invested == Decimal("50000")
    assert ledger.remaining_capacity == Decimal("0")

    restarted = PortfolioExposureLedger(path, Decimal("50000"))
    assert restarted.total_invested == Decimal("50000")
    try:
        restarted.allocate("overflow", Decimal("1"))
        raise AssertionError("Portfolio ceiling must fail closed.")
    except RiskRejected:
        pass

    assert restarted.release("bot-000", Decimal("250")) == Decimal("250")
    assert restarted.total_invested == Decimal("49750")
    restarted.allocate("replacement", Decimal("250"))
    assert restarted.total_invested == Decimal("50000")

with tempfile.TemporaryDirectory() as root:
    path = Path(root) / "exposure.json"
    path.write_text('{"bad": "-1"}')
    try:
        PortfolioExposureLedger(path, Decimal("50000"))
        raise AssertionError("Negative persisted exposure must fail closed.")
    except RiskRejected:
        pass

print("PORTFOLIO EXPOSURE LEDGER: PASS")
print("100 x $500 invested ceiling: PASS")
print("Restart persistence: PASS")
print("Partial release/reallocation: PASS")
print("Corrupt/invalid state fails closed: PASS")
print("Real Alpaca order submitted: NO")
