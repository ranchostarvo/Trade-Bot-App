from dataclasses import dataclass
from decimal import Decimal


class RiskRejected(RuntimeError):
    pass


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: str
    quantity: Decimal
    estimated_price: Decimal
    requested_notional: Decimal | None = None

    @property
    def notional(self) -> Decimal:
        if self.requested_notional is not None:
            return self.requested_notional
        return self.quantity * self.estimated_price


@dataclass(frozen=True)
class AccountRiskState:
    start_of_day_equity: Decimal
    current_equity: Decimal

    @property
    def daily_loss(self) -> Decimal:
        loss = self.start_of_day_equity - self.current_equity
        return max(loss, Decimal("0"))

    @property
    def daily_loss_pct(self) -> Decimal:
        if self.start_of_day_equity <= 0:
            raise RiskRejected(
                "Start-of-day equity must be greater than zero."
            )

        return (
            self.daily_loss / self.start_of_day_equity
        ) * Decimal("100")


@dataclass
class RiskConfig:
    max_order_notional: Decimal = Decimal("500")
    max_daily_loss_pct: Decimal = Decimal("2.5")
    trading_enabled: bool = False
    dry_run: bool = True


class RiskEngine:
    def __init__(self, config=None):
        self.config = config or RiskConfig()

    def validate_daily_loss(self, account: AccountRiskState):
        loss_pct = account.daily_loss_pct

        if loss_pct >= self.config.max_daily_loss_pct:
            raise RiskRejected(
                f"Daily loss limit reached: {loss_pct:.2f}% "
                f">= {self.config.max_daily_loss_pct}%."
            )

        return loss_pct

    def validate(
        self,
        order: OrderRequest,
        account: AccountRiskState | None = None,
    ):
        symbol = order.symbol.strip().upper()
        side = order.side.strip().lower()

        if not symbol:
            raise RiskRejected("Symbol is required.")

        if side not in {"buy", "sell"}:
            raise RiskRejected("Side must be buy or sell.")

        if order.requested_notional is None and order.quantity <= 0:
            raise RiskRejected("Quantity must be greater than zero.")

        if order.requested_notional is not None:
            if order.requested_notional <= 0:
                raise RiskRejected("Requested notional must be greater than zero.")
            if order.quantity != 0:
                raise RiskRejected(
                    "Notional orders must use quantity=0 to avoid ambiguous sizing."
                )

        if order.estimated_price <= 0:
            raise RiskRejected("Estimated price must be greater than zero.")

        if order.notional > self.config.max_order_notional:
            raise RiskRejected(
                f"Order notional ${order.notional} exceeds "
                f"${self.config.max_order_notional} limit."
            )

        daily_loss_pct = None

        if account is not None:
            daily_loss_pct = self.validate_daily_loss(account)

        return {
            "approved": True,
            "symbol": symbol,
            "side": side,
            "quantity": str(order.quantity),
            "requested_notional": (
                str(order.requested_notional)
                if order.requested_notional is not None
                else None
            ),
            "estimated_price": str(order.estimated_price),
            "notional": str(order.notional),
            "daily_loss_pct": (
                str(daily_loss_pct)
                if daily_loss_pct is not None
                else None
            ),
            "dry_run": self.config.dry_run,
            "trading_enabled": self.config.trading_enabled,
        }
