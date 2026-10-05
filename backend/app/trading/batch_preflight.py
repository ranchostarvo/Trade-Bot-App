from .risk import RiskRejected


class BotBatchPreflight:
    """Validate a complete bot batch before the first execution side effect."""

    def __init__(self, registry, runtime, max_bots=100):
        self.registry = registry
        self.runtime = runtime
        self.max_bots = int(max_bots)

    def validate(self, requests):
        requests = list(requests)
        if len(requests) > self.max_bots:
            raise RiskRejected("Bot batch exceeds configured bot limit.")
        status = self.runtime.status()
        if not status.started or not status.ready:
            raise RiskRejected("Runtime is not ready for bot batch execution.")

        seen_bots = set()
        seen_orders = set()
        total_notional = 0
        for request in requests:
            bot_id = str(request.bot_id or "").strip()
            client_id = str(request.client_order_id or "").strip()
            if not bot_id or not client_id:
                raise RiskRejected("Bot ID and client order ID are required.")
            if bot_id in seen_bots or client_id in seen_orders:
                raise RiskRejected("Duplicate bot or client order ID in batch.")
            seen_bots.add(bot_id)
            seen_orders.add(client_id)

            bot = self.registry.get(bot_id)
            if bot is None:
                raise RiskRejected(f"Bot {bot_id} is not registered.")
            if not bot.enabled:
                raise RiskRejected(f"Bot {bot_id} is disabled.")
            if str(request.order.symbol).upper() != bot.symbol:
                raise RiskRejected(f"Bot {bot_id} symbol does not match registry.")
            total_notional += request.order.notional

        return {"bots": len(requests), "requested_notional": total_notional}
