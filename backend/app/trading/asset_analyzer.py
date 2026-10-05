from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .risk import RiskRejected


@dataclass(frozen=True)
class AssetAnalysis:
    symbol: str
    asset_class: str
    price: Decimal
    max_order_notional: Decimal
    max_quantity: Decimal


class AssetAnalyzer:
    """Deterministic Paper-v1 sizing analysis; never submits orders."""

    VALID_ASSET_CLASSES = {"stock", "etf", "crypto"}

    def analyze(self, symbol, asset_class, price, max_order_notional):
        symbol = str(symbol).strip().upper()
        asset_class = str(asset_class).strip().lower()
        if not symbol:
            raise RiskRejected("Asset symbol is required.")
        if asset_class not in self.VALID_ASSET_CLASSES:
            raise RiskRejected("Unsupported asset class.")
        try:
            price = Decimal(str(price))
            ceiling = Decimal(str(max_order_notional))
        except (InvalidOperation, ValueError):
            raise RiskRejected("Invalid asset analysis numeric value.")
        if price <= 0 or ceiling <= 0:
            raise RiskRejected("Asset price and order ceiling must be positive.")
        quantity = ceiling / price
        return AssetAnalysis(symbol, asset_class, price, ceiling, quantity)
