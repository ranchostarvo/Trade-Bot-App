from dataclasses import dataclass


@dataclass(frozen=True)
class VirtualDayReport:
    requested: int
    succeeded: int
    rejected: int
    duplicate_submissions: int
    live_orders: int


class VirtualTradingDay:
    """Deterministic scale harness; never talks to Alpaca."""

    def __init__(self, orchestrator, broker):
        self.orchestrator = orchestrator
        self.broker = broker

    def run(self, requests):
        requests = list(requests)
        before = len(self.broker.orders)
        results = self.orchestrator.execute_batch(requests)
        after = len(self.broker.orders)
        succeeded = sum(1 for item in results if item["ok"])
        rejected = len(results) - succeeded
        client_ids = [o.get("client_order_id") for o in self.broker.orders.values()]
        duplicates = len(client_ids) - len(set(client_ids))
        return VirtualDayReport(
            requested=len(requests),
            succeeded=succeeded,
            rejected=rejected,
            duplicate_submissions=duplicates,
            live_orders=after - before,
        )
