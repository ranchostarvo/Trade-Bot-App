from dataclasses import dataclass
from decimal import Decimal

from .order_state import OrderState


class SettlementRejected(RuntimeError):
    pass


@dataclass
class ExposureSettlement:
    """Applies exposure changes only at explicit lifecycle settlement points."""

    resources: object

    def settle_buy(self, managed_order, bot_id, request):
        if managed_order.state is not OrderState.FILLED:
            raise SettlementRejected(
                "BUY exposure settlement requires FILLED order state."
            )
        self.resources.reserve_symbol_exposure(
            bot_id, request.symbol, request.notional
        )

    def settle_sell(self, managed_order, bot_id, request):
        if managed_order.state is not OrderState.FILLED:
            raise SettlementRejected(
                "SELL exposure settlement requires FILLED order state."
            )
        self.resources.release_symbol_exposure(
            bot_id, request.symbol, request.notional
        )
