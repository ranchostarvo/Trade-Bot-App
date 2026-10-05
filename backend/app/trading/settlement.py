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
        self.resources.settle_pending_buy(managed_order.order_id)

    def settle_sell(self, managed_order, bot_id, request):
        if managed_order.state is not OrderState.FILLED:
            raise SettlementRejected(
                "SELL exposure settlement requires FILLED order state."
            )
        if not self._claim(managed_order.order_id, "FILLED_SELL"):
            return False
        try:
            self.resources.release_symbol_exposure(
                bot_id, request.symbol, request.notional
            )
        except Exception:
            # Claim-before-effect prevents duplicate financial effects, but a
            # failed effect requires operator reconciliation before retry.
            raise
        return True


    def settle_terminal(self, managed_order):
        if managed_order.state not in (OrderState.REJECTED, OrderState.CANCELED):
            raise SettlementRejected(
                "Pending exposure release requires REJECTED or CANCELED order state."
            )
        self.resources.release_pending_exposure(managed_order.order_id)
