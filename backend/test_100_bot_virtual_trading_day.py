from dataclasses import dataclass

from app.trading.bot_orchestrator import BotOrder, BotOrchestrator
from app.trading.virtual_broker import VirtualBroker
from app.trading.virtual_trading_day import VirtualTradingDay


@dataclass
class Order:
    symbol: str
    side: str = "buy"


class Runtime:
    def __init__(self, broker):
        self.broker = broker

    def execute(self, order, client_order_id):
        return self.broker.submit_order({
            "symbol": order.symbol,
            "side": order.side,
            "client_order_id": client_order_id,
        })


def make_requests():
    return [
        BotOrder(f"bot-{i:03d}", Order(f"SYM{i:03d}"), f"day-order-{i:03d}")
        for i in range(100)
    ]


def run():
    broker = VirtualBroker()
    day = VirtualTradingDay(BotOrchestrator(Runtime(broker)), broker)
    report = day.run(make_requests())
    assert report.requested == 100
    assert report.succeeded == 100
    assert report.rejected == 0
    assert report.duplicate_submissions == 0
    assert report.live_orders == 100
    assert len(broker.orders) == 100

    for i in range(0, 100, 2):
        broker.transition(f"day-order-{i:03d}", "filled", "1", "100")
    assert broker.expire_open_orders() == 50
    assert sum(1 for order in broker.orders.values() if order["status"] == "filled") == 50
    assert sum(1 for order in broker.orders.values() if order["status"] == "expired") == 50

    # A replay of the same batch must not silently create additional broker
    # records. The virtual broker's client IDs remain the deterministic identity.
    replay = day.run(make_requests())
    assert replay.duplicate_submissions == 0
    assert len(broker.orders) == 100

    print("100-BOT VIRTUAL TRADING DAY: PASS")


if __name__ == "__main__":
    run()
