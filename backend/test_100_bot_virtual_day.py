from types import SimpleNamespace
from app.trading.bot_orchestrator import BotOrder, BotOrchestrator
from app.trading.virtual_broker import VirtualBroker
from app.trading.virtual_trading_day import VirtualTradingDay

class Runtime:
    def __init__(self,broker): self.broker=broker
    def execute(self,order,client_order_id=None):
        return self.broker.submit_order({"symbol":order.symbol,"side":"buy","qty":"1","client_order_id":client_order_id})

broker=VirtualBroker()
runtime=Runtime(broker)
orchestrator=BotOrchestrator(runtime,max_bots=100)
requests=[BotOrder(f"bot-{i:03d}",SimpleNamespace(symbol="SPY"),f"cid-{i:03d}") for i in range(100)]
report=VirtualTradingDay(orchestrator,broker).run(requests)
assert report.requested==100
assert report.succeeded==100
assert report.rejected==0
assert report.duplicate_submissions==0
assert report.live_orders==100
assert len(broker.orders)==100
print("100-BOT VIRTUAL TRADING DAY: PASS")
print("Duplicate submissions: 0")
print("Real Alpaca orders: 0")
