from decimal import Decimal

from .risk import RiskRejected


class SellTransitionRecovery:
    """Recover or fail closed on interrupted sell cost-basis transitions."""

    def __init__(self, journal, checkpoints, allocation_book):
        self.journal = journal
        self.checkpoints = checkpoints
        self.allocation_book = allocation_book

    def reconcile(self):
        recovered = []
        for order_id, record in self.journal.pending().items():
            try:
                start = Decimal(str(record["from_qty"]))
                end = Decimal(str(record["to_qty"]))
                status = str(record["status"])
                symbol = str(record["symbol"]).upper()
            except Exception as exc:
                raise RiskRejected(f"Invalid pending sell transition: {exc}") from exc

            checkpoint_delta = self.checkpoints.delta(order_id, end)
            if status == "applied":
                # Exposure was already released; only durable checkpoint/cleanup
                # remains. Re-applying the sell would double-release cost basis.
                if checkpoint_delta > 0:
                    self.checkpoints.commit(order_id, end)
                self.journal.complete(order_id)
                recovered.append(order_id)
                continue

            if status == "prepared":
                # We cannot prove whether the exposure write happened before a
                # crash. Never guess or replay a potentially destructive sell.
                raise RiskRejected(
                    f"Ambiguous prepared sell transition for {order_id}; "
                    "manual/state reconciliation required."
                )

            raise RiskRejected(f"Unknown sell transition status for {order_id}.")
        return recovered
