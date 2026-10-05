from decimal import Decimal

from .risk import RiskRejected


class BuyTransitionRecovery:
    """Deterministically finish or fail closed on interrupted buy transitions."""

    def __init__(self, journal, reservations, exposure, position_allocations, checkpoints):
        self.journal = journal
        self.reservations = reservations
        self.exposure = exposure
        self.position_allocations = position_allocations
        self.checkpoints = checkpoints

    def reconcile(self):
        recovered = 0
        for order_id, entry in self.journal.pending().items():
            status = entry.get("status")
            allocation_id = entry["allocation_id"]
            notional = Decimal(entry["notional"])
            quantity = Decimal(entry["quantity"])
            symbol = entry["symbol"]
            exposure_value = self.exposure.get(allocation_id)
            allocation = self.position_allocations.get(allocation_id)

            if status == "prepared":
                if exposure_value == 0:
                    raise RiskRejected(
                        "Prepared buy transition is ambiguous before exposure commit; "
                        "manual reconciliation is required."
                    )
                if exposure_value != notional:
                    raise RiskRejected("Buy transition exposure does not match journal.")
                self.journal.mark_exposure_applied(order_id)
                status = "exposure_applied"

            if status == "exposure_applied":
                if exposure_value != notional:
                    raise RiskRejected("Buy transition exposure is missing or inconsistent.")
                if allocation is None:
                    self.position_allocations.record_allocated_buy(
                        allocation_id, symbol, quantity, notional
                    )
                else:
                    if (
                        allocation.symbol != symbol
                        or allocation.quantity != quantity
                        or allocation.invested_notional != notional
                    ):
                        raise RiskRejected("Buy transition allocation conflicts with journal.")
                self.journal.mark_allocation_applied(order_id)
                status = "allocation_applied"

            if status == "allocation_applied":
                # Reservation mutation occurred with exposure allocation. We only
                # advance the fill checkpoint after both persistent ledgers agree.
                checkpoint = self.checkpoints.recovery_state(order_id)
                if checkpoint is None:
                    raise RiskRejected(
                        "Interrupted buy transition lacks cumulative checkpoint target; "
                        "manual reconciliation is required."
                    )
                checkpoint_qty, checkpoint_value = checkpoint
                if checkpoint_qty < quantity or checkpoint_value < notional:
                    raise RiskRejected(
                        "Buy transition checkpoint is inconsistent with journal."
                    )
                self.journal.complete(order_id)
                recovered += 1
            elif status not in ("prepared", "exposure_applied", "allocation_applied"):
                raise RiskRejected("Unknown buy transition journal status.")
        return recovered
