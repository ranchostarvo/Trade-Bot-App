from app.trading.risk import RiskRejected
from app.trading.risk_profiles import get_risk_profile

expected = {
    "conservative": ("250", "1.0"),
    "moderate": ("375", "1.75"),
    "aggressive": ("500", "2.5"),
}
for name, values in expected.items():
    profile = get_risk_profile(name)
    assert str(profile.max_order_notional) == values[0]
    assert str(profile.max_daily_loss_pct) == values[1]

try:
    get_risk_profile("unsupported")
    raise AssertionError("Unsupported profile must fail closed.")
except RiskRejected:
    pass

print("RISK PROFILES: PASS")
print("Maximum aggressive daily loss remains 2.5%: PASS")
print("Real Alpaca order submitted: NO")
