"""Controlled Alpaca Paper-v1 validation entry point.

Requires explicit operator authorization before invocation. It refuses live
configuration and routes the order through ExecutionEngine rather than calling
AlpacaClient.submit_order directly.
"""
from decimal import Decimal
from uuid import uuid4

from app.brokers.alpaca import AlpacaClient
from app.trading.risk import OrderRequest, RiskRejected


def validate_paper_environment(client):
    cfg = client.config
    if not cfg.paper or cfg.base_url != "https://paper-api.alpaca.markets":
        raise RiskRejected("Paper validation requires the exact Alpaca paper endpoint.")
    account = client.get_account()
    if account.get("trading_blocked") or account.get("account_blocked"):
        raise RiskRejected("Alpaca paper account is blocked.")
    return account


def run_authorized_validation(engine, client, symbol="SPY", notional="10"):
    account = validate_paper_environment(client)
    amount = Decimal(str(notional))
    if amount <= 0 or amount > Decimal("10"):
        raise RiskRejected("Controlled validation notional must be > 0 and <= $10.")
    order = OrderRequest(
        symbol=str(symbol).upper(),
        side="buy",
        quantity=Decimal("0"),
        estimated_price=Decimal("1"),
        requested_notional=amount,
    )
    client_order_id = "paper-rc-" + uuid4().hex[:20]
    result = engine.execute(order, client_order_id=client_order_id)
    return {
        "paper": True,
        "account_status": account.get("status"),
        "client_order_id": client_order_id,
        "result": result,
    }


if __name__ == "__main__":
    raise SystemExit(
        "Safety stop: construct the production RC runtime and invoke "
        "run_authorized_validation(engine, client) explicitly."
    )
