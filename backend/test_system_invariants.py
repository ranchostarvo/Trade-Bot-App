from decimal import Decimal
from types import SimpleNamespace
from app.trading.system_invariants import SystemInvariantChecker
from app.trading.risk import RiskRejected

registry=SimpleNamespace(all=lambda: [None]*100)
capital=SimpleNamespace(allocated=Decimal("10000"))
exposure=SimpleNamespace(total_invested=Decimal("40000"))
assert SystemInvariantChecker(capital,exposure,registry,50000).check()["combined_capital_ceiling"]
exposure.total_invested=Decimal("40000.01")
try:
    SystemInvariantChecker(capital,exposure,registry,50000).check()
    raise AssertionError("ceiling violation must fail")
except RiskRejected: pass
print("SYSTEM INVARIANTS: PASS")
