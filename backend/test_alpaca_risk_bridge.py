from app.brokers.alpaca import AlpacaClient
from app.trading.account_state import (
    AlpacaAccountStateProvider,
)
from app.trading.risk import RiskEngine


print("=== TRADING APP v2.0 / ALPACA RISK BRIDGE ===")

client = AlpacaClient()
provider = AlpacaAccountStateProvider(client)
risk = RiskEngine()

account = provider.get_risk_state()
loss_pct = risk.validate_daily_loss(account)

print(
    "Start equity:",
    account.start_of_day_equity,
)
print(
    "Current equity:",
    account.current_equity,
)
print(
    "Daily loss:",
    account.daily_loss,
)
print(
    "Daily loss %:",
    f"{loss_pct:.2f}%",
)

assert loss_pct < risk.config.max_daily_loss_pct

print("Alpaca account data: PASS")
print("Daily-loss gate: PASS")
print("No order submitted: PASS")
print("RESULT: PASS")
