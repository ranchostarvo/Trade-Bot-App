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
        self.resources.settle_pending_buy(managed_order.order_id)

    def settle_sell(self, managed_order, bot_id, request):
        if managed_order.state is not OrderState.FILLED:
            raise SettlementRejected(
                "SELL exposure settlement requires FILLED order state."
            )
        self.resources.release_symbol_exposure(
            bot_id, request.symbol, request.notional
        )


    def settle_terminal(self, managed_order):
        if managed_order.state not in (OrderState.REJECTED, OrderState.CANCELED):
            raise SettlementRejected(
                "Pending exposure release requires REJECTED or CANCELED order state."
            )
        self.resources.release_pending_exposure(managed_order.order_id)
