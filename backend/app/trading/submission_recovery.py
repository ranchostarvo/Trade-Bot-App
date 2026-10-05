from .order_tracker import TERMINAL_ORDER_STATUSES


class SubmissionRecovery:
    def __init__(self, broker, submission_ledger, capital_coordinator=None):
        self.broker = broker
        self.submission_ledger = submission_ledger
        self.capital_coordinator = capital_coordinator

    def resolve(self, client_order_id):
        client_order_id = str(client_order_id or "").strip()
        if not client_order_id:
            raise ValueError("client_order_id is required.")

        reservation = self.submission_ledger.get(client_order_id)
        if reservation is None:
            raise RuntimeError(
                "Cannot recover an order without a persisted reservation."
            )

        if (
            self.capital_coordinator is not None
            and self.capital_coordinator.get(client_order_id) <= 0
        ):
            raise RuntimeError(
                "Cannot recover ambiguous order without its capital reservation."
            )

        # Read-only broker lookup. A reserved id must never be blindly
        # resubmitted after an ambiguous network failure.
        raw = self.broker.get_order_by_client_id(client_order_id)
        broker_id = str(raw.get("id") or "").strip()
        status = str(raw.get("status") or "").strip().lower()
        if not broker_id or not status:
            raise RuntimeError("Broker returned incomplete recovery data.")

        capital_released = False
        if (
            self.capital_coordinator is not None
            and status in TERMINAL_ORDER_STATUSES
        ):
            self.capital_coordinator.release(client_order_id)
            capital_released = True

        return {
            "client_order_id": client_order_id,
            "broker_order_id": broker_id,
            "status": status,
            "recovered": True,
            "capital_released": capital_released,
        }
