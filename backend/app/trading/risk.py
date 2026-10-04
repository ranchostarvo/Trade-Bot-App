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
class AccountRiskState:
    start_of_day_equity: Decimal
    current_equity: Decimal

    @property
    def daily_loss_pct(self) -> Decimal:
        if self.start_of_day_equity <= 0:
            raise RiskRejected("Start-of-day equity must be greater than zero.")
        loss = self.start_of_day_equity - self.current_equity
        if loss <= 0:
            return Decimal("0")
        return (loss / self.start_of_day_equity) * Decimal("100")


@dataclass(frozen=True)
class RiskConfig:
    max_order_notional: Decimal = Decimal("500")
    max_daily_loss_pct: Decimal = Decimal("2.5")
    trading_enabled: bool = False
    dry_run: bool = True


class RiskEngine:
    def __init__(self, config=None, kill_switch=None):
        self.config = config or RiskConfig()
        self.kill_switch = kill_switch

    def validate(self, order: OrderRequest, account_state=None):
        if self.kill_switch is not None and self.kill_switch.engaged:
            raise RiskRejected("Global kill switch is engaged.")

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

        if account_state is not None:
            loss_pct = account_state.daily_loss_pct
            if loss_pct >= self.config.max_daily_loss_pct:
                if self.kill_switch is not None:
                    self.kill_switch.engage(
                        f"Daily loss limit reached: {loss_pct:.4f}%"
                    )
                raise RiskRejected(
                    f"Daily loss {loss_pct:.4f}% reached the "
                    f"{self.config.max_daily_loss_pct}% limit."
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
