from dataclasses import dataclass
from decimal import Decimal


class RiskRejected(RuntimeError):
    """Raised when an order violates a hard risk control."""


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: str
    quantity: Decimal
    estimated_price: Decimal

    @property
    def notional(self) -> Decimal:
        return self.quantity * self.estimated_price


@dataclass(frozen=True)
class RiskConfig:
    max_order_notional: Decimal = Decimal("500")
    max_daily_loss_pct: Decimal = Decimal("2.5")
    trading_enabled: bool = False
    dry_run: bool = True


class RiskEngine:
    def __init__(self, config=None):
        self.config = config or RiskConfig()

    def validate(self, order: OrderRequest):
        symbol = order.symbol.strip().upper()
        side = order.side.strip().lower()

        if not symbol:
            raise RiskRejected("Symbol is required.")
        if side not in {"buy", "sell"}:
            raise RiskRejected("Side must be buy or sell.")
        if order.quantity <= 0:
            raise RiskRejected("Quantity must be greater than zero.")
        if order.estimated_price <= 0:
            raise RiskRejected("Estimated price must be greater than zero.")
        if order.notional > self.config.max_order_notional:
            raise RiskRejected(
                f"Order notional ${order.notional} exceeds "
                f"${self.config.max_order_notional} limit."
            )

        return {
            "approved": True,
            "symbol": symbol,
            "side": side,
            "quantity": str(order.quantity),
            "estimated_price": str(order.estimated_price),
            "notional": str(order.notional),
            "dry_run": self.config.dry_run,
            "trading_enabled": self.config.trading_enabled,
        }
