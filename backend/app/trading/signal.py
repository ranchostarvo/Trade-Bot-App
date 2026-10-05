from dataclasses import dataclass
from decimal import Decimal

from .risk import OrderRequest


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    price: Decimal
    previous_close: Decimal

    def __post_init__(self):
        if not self.symbol.strip():
            raise ValueError("Symbol is required.")
        if self.price <= 0 or self.previous_close <= 0:
            raise ValueError("Market prices must be greater than zero.")

    @property
    def change_pct(self) -> Decimal:
        return (
            (self.price - self.previous_close)
            / self.previous_close
            * Decimal("100")
        )


@dataclass(frozen=True)
class StrategyConfig:
    entry_change_pct: Decimal = Decimal("-1.0")
    exit_change_pct: Decimal = Decimal("1.0")
    proposed_notional: Decimal = Decimal("100")


@dataclass(frozen=True)
class Signal:
    symbol: str
    action: str
    reason: str
    reference_price: Decimal


class ThresholdStrategy:
    """Deterministic development strategy used to exercise the pipeline."""

    def __init__(self, config=None):
        self.config = config or StrategyConfig()

    def evaluate(self, market: MarketSnapshot) -> Signal:
        change = market.change_pct
        symbol = market.symbol.strip().upper()
        if change <= self.config.entry_change_pct:
            return Signal(
                symbol, "BUY", f"change_pct={change:.4f}", market.price
            )
        if change >= self.config.exit_change_pct:
            return Signal(
                symbol, "SELL", f"change_pct={change:.4f}", market.price
            )
        return Signal(
            symbol, "HOLD", f"change_pct={change:.4f}", market.price
        )

    def propose_order(self, signal: Signal) -> OrderRequest | None:
        if signal.action == "HOLD":
            return None
        quantity = self.config.proposed_notional / signal.reference_price
        return OrderRequest(
            symbol=signal.symbol,
            side=signal.action.lower(),
            quantity=quantity,
            estimated_price=signal.reference_price,
        )
