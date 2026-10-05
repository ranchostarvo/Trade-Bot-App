from decimal import Decimal

from .risk import RiskRejected
from .risk_profiles import get_risk_profile


class BotBatchPreflight:
    """Validate a complete bot batch before the first execution side effect."""

    def __init__(self, registry, runtime, max_bots=100, capital_coordinator=None, exposure_ledger=None):
        self.registry = registry
        self.runtime = runtime
        self.max_bots = int(max_bots)
        self.capital_coordinator = capital_coordinator
        self.exposure_ledger = exposure_ledger

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
            notional = Decimal(str(request.order.notional))
            profile = get_risk_profile(bot.risk_profile)
            if notional <= 0:
                raise RiskRejected(f"Bot {bot_id} requested invalid notional.")
            if notional > profile.max_order_notional:
                raise RiskRejected(
                    f"Bot {bot_id} order exceeds {profile.name} profile limit."
                )
            total_notional += notional

        if self.capital_coordinator is not None and self.exposure_ledger is not None:
            invested = self.exposure_ledger.total_invested
            reserved = self.capital_coordinator.total_reserved
            ceiling = self.capital_coordinator.config.max_total_allocated
            if invested + reserved + total_notional > ceiling:
                raise RiskRejected("Bot batch exceeds combined portfolio capital ceiling.")

        return {"bots": len(requests), "requested_notional": total_notional}
