from dataclasses import dataclass

from app.brokers.alpaca import AlpacaClient
from app.storage import SQLiteStore
from app.trading.reconciliation import AlpacaReconciler
from app.trading.runtime import TradingRuntime


class BootstrapBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class BrokerBootstrap:
    runtime: TradingRuntime
    reconciler: AlpacaReconciler

    @classmethod
    def build(cls, store=None, client=None):
        """Build a read-only broker-backed runtime. Never submits orders."""
        client = client or AlpacaClient()
        reconciler = AlpacaReconciler(client)
        account = reconciler.account_snapshot()

        if account.account_blocked or account.trading_blocked:
            raise BootstrapBlocked("Broker account is blocked from trading.")
        if account.cash <= 0 or account.equity <= 0:
            raise BootstrapBlocked(
                "Broker account cash and equity must be positive."
            )

        store = store or SQLiteStore()
        runtime = TradingRuntime.build(
            account_cash=account.cash,
            account_equity=account.equity,
            reconciler=reconciler,
            store=store,
        )
        return cls(runtime=runtime, reconciler=reconciler)
