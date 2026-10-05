class SubmissionRecovery:
    def __init__(self, broker, submission_ledger):
        self.broker = broker
        self.submission_ledger = submission_ledger

    def resolve(self, client_order_id):
        client_order_id = str(client_order_id or "").strip()
        if not client_order_id:
            raise ValueError("client_order_id is required.")

        reservation = self.submission_ledger.get(client_order_id)
        if reservation is None:
            raise RuntimeError(
                "Cannot recover an order without a persisted reservation."
            )

        # Read-only broker lookup. A reserved id must never be blindly
        # resubmitted after an ambiguous network failure.
        raw = self.broker.get_order_by_client_id(client_order_id)
        broker_id = str(raw.get("id") or "").strip()
        status = str(raw.get("status") or "").strip().lower()
        if not broker_id or not status:
            raise RuntimeError("Broker returned incomplete recovery data.")

        return {
            "client_order_id": client_order_id,
            "broker_order_id": broker_id,
            "status": status,
            "recovered": True,
        }
