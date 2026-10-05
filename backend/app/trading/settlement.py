from dataclasses import dataclass
from decimal import Decimal

from .order_state import OrderState


class SettlementRejected(RuntimeError):
    pass


@dataclass
class ExposureSettlement:
    """Applies exposure changes only at explicit lifecycle settlement points."""

    resources: object

    def _claim(self, order_id, outcome):
        store = getattr(self.resources, "store", None)
        if store is None:
            return True
        return store.claim_order_settlement(order_id, outcome)

    def settle_buy(self, managed_order, bot_id, request):
        if managed_order.state is not OrderState.FILLED:
            raise SettlementRejected(
                "BUY exposure settlement requires FILLED order state."
            )
        return self.resources.settle_pending_buy(managed_order.order_id)

    def settle_sell(self, managed_order, bot_id, request):
        if managed_order.state is not OrderState.FILLED:
            raise SettlementRejected(
                "SELL exposure settlement requires FILLED order state."
            )
        store = getattr(self.resources, "store", None)
        if store is not None:
            return store.settle_filled_sell_atomically(
                managed_order.order_id,
                bot_id,
                request.symbol,
                request.notional,
            )
        self.resources.release_symbol_exposure(
            bot_id, request.symbol, request.notional
        )
        return True


    def settle_terminal(self, managed_order):
        if managed_order.state not in (OrderState.REJECTED, OrderState.CANCELED):
            raise SettlementRejected(
                "Pending exposure release requires REJECTED or CANCELED order state."
            )
        store = getattr(self.resources, "store", None)\n        if store is not None:\n            return store.settle_terminal_pending_atomically(\n                managed_order.order_id, managed_order.state.value\n            )\n        self.resources.release_pending_exposure(managed_order.order_id)\n        return True
