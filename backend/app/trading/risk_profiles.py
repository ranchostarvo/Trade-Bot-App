from dataclasses import dataclass
from decimal import Decimal

from .risk import RiskRejected


@dataclass(frozen=True)
class BotRiskProfile:
    name: str
    max_order_notional: Decimal
    max_daily_loss_pct: Decimal


PROFILES = {
    "conservative": BotRiskProfile("conservative", Decimal("250"), Decimal("1.0")),
    "moderate": BotRiskProfile("moderate", Decimal("375"), Decimal("1.75")),
    "aggressive": BotRiskProfile("aggressive", Decimal("500"), Decimal("2.5")),
}


def get_risk_profile(name):
    key = str(name or "").strip().lower()
    try:
        return PROFILES[key]
    except KeyError as exc:
        raise RiskRejected("Unsupported bot risk profile.") from exc
