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

    @classmethod
    def from_reconciler(cls, store, reconciler, exposure_config=None):
        account = reconciler.account_snapshot()
        if account.account_blocked or account.trading_blocked:
            raise DurableResourceRejected(
                "Broker account is blocked from resource allocation."
            )
        if account.cash < 0 or account.equity <= 0:
            raise DurableResourceRejected(
                "Broker account returned invalid cash or equity."
            )
        return cls(
            store=store,
            account_cash=account.cash,
            account_equity=account.equity,
            exposure_config=exposure_config or ExposureConfig(),
        )

    def reserve_bot_capital(self, bot_id: str, amount: Decimal) -> None:
        if not self.store.reserve_capital_atomically(
            bot_id, amount, self.account_cash
        ):
            raise DurableResourceRejected(
                f"Capital reservation rejected for bot {bot_id}."
            )

    def release_bot_capital(self, bot_id: str) -> None:
        if not self.store.release_capital_atomically(bot_id):
            raise DurableResourceRejected(
                f"No durable capital reservation exists for bot {bot_id}."
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


    def release_symbol_exposure(
        self, bot_id: str, symbol: str, notional=None
    ) -> None:
        if not self.store.release_exposure_atomically(
            bot_id, symbol, notional
        ):
            raise DurableResourceRejected(
                f"No durable exposure reservation exists for bot {bot_id} {symbol}."
            )


    def reserve_pending_exposure(
        self, order_id: str, bot_id: str, symbol: str, notional: Decimal
    ) -> None:
        if not self.store.reserve_pending_exposure_with_limits(
            order_id,
            bot_id,
            symbol,
            notional,
            self.account_equity,
            self.exposure_config.max_symbol_notional,
            self.exposure_config.max_symbol_pct,
        ):
            raise DurableResourceRejected(
                f"Pending exposure rejected for order {order_id}."
            )

    def release_pending_exposure(self, order_id: str) -> None:
        if not self.store.release_pending_exposure(order_id):
            raise DurableResourceRejected(
                f"No pending exposure exists for order {order_id}."
            )


    def settle_pending_buy(self, order_id: str) -> bool:
        try:
            result = self.store.settle_pending_buy_atomically(order_id)
        except ValueError as exc:
            raise DurableResourceRejected(str(exc)) from exc
        if result is False and self.store.load_order_settlement(order_id) is None:
            raise DurableResourceRejected(
                f"No pending BUY exposure exists for order {order_id}."
            )
        return result
