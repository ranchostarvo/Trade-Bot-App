from dataclasses import dataclass
from decimal import Decimal

from .portfolio import ExposureConfig


class DurableResourceRejected(RuntimeError):
    pass


@dataclass
class DurableResourceCoordinator:
    """Database-backed shared resource gate for multi-worker bot fleets."""

    store: object
    account_cash: Decimal
    account_equity: Decimal
    exposure_config: ExposureConfig = ExposureConfig()

    def reserve_bot_capital(self, bot_id: str, amount: Decimal) -> None:
        if not self.store.reserve_capital_atomically(
            bot_id, amount, self.account_cash
        ):
            raise DurableResourceRejected(
                f"Capital reservation rejected for bot {bot_id}."
            )

    def reserve_symbol_exposure(
        self, bot_id: str, symbol: str, notional: Decimal
    ) -> None:
        if not self.store.reserve_exposure_atomically(
            bot_id,
            symbol,
            notional,
            self.account_equity,
            self.exposure_config.max_symbol_notional,
            self.exposure_config.max_symbol_pct,
        ):
            raise DurableResourceRejected(
                f"Exposure reservation rejected for bot {bot_id} {symbol}."
            )
