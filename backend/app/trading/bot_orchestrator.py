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

    def __init__(self, runtime, max_bots=100, stop_on_rejection=True, batch_preflight=None):
        self.runtime = runtime
        self.max_bots = int(max_bots)
        self.stop_on_rejection = bool(stop_on_rejection)
        self.batch_preflight = batch_preflight
        if self.max_bots < 1 or self.max_bots > 100:
            raise ValueError("max_bots must be between 1 and 100.")

    def execute_batch(self, requests):
        requests = list(requests)
        if len(requests) > self.max_bots:
            raise RiskRejected("Bot batch exceeds configured bot limit.")
        if self.batch_preflight is not None:
            self.batch_preflight.validate(requests)

        # Validate the complete batch before the first execution. Structural
        # errors must never create a partially executed batch.
        seen_bots = set()
        seen_orders = set()
        prepared = []
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
            prepared.append((bot_id, client_order_id, request.order))

        results = []
        for bot_id, client_order_id, order in prepared:
            try:
                result = self.runtime.execute(order, client_order_id=client_order_id)
                results.append({"bot_id": bot_id, "ok": True, "result": result})
            except RiskRejected as exc:
                results.append({"bot_id": bot_id, "ok": False, "error": str(exc)})
                if self.stop_on_rejection:
                    break
        return results
