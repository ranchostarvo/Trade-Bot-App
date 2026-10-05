from dataclasses import dataclass
from decimal import Decimal

from .risk import RiskRejected


@dataclass(frozen=True)
class BotOrder:
    bot_id: str
    order: object
    client_order_id: str


class BotOrchestrator:
    """Deterministic bounded fan-out for many independently configured bots."""

    def __init__(self, runtime, max_bots=100):
        self.runtime = runtime
        self.max_bots = int(max_bots)
        if self.max_bots < 1 or self.max_bots > 100:
            raise ValueError("max_bots must be between 1 and 100.")

    def execute_batch(self, requests):
        requests = list(requests)
        if len(requests) > self.max_bots:
            raise RiskRejected("Bot batch exceeds configured bot limit.")

        seen_bots = set()
        seen_orders = set()
        results = []
        for request in requests:
            bot_id = str(request.bot_id or "").strip()
            client_order_id = str(request.client_order_id or "").strip()
            if not bot_id or not client_order_id:
                raise RiskRejected("Bot ID and client order ID are required.")
            if bot_id in seen_bots:
                raise RiskRejected("Duplicate bot ID in execution batch.")
            if client_order_id in seen_orders:
                raise RiskRejected("Duplicate client order ID in execution batch.")
            seen_bots.add(bot_id)
            seen_orders.add(client_order_id)

            # Sequential fan-out is intentional for v1: shared portfolio capital
            # reservations are observed before the next bot is allowed to execute.
            results.append({
                "bot_id": bot_id,
                "result": self.runtime.execute(
                    request.order,
                    client_order_id=client_order_id,
                ),
            })
        return results
