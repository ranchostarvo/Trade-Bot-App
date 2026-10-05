from types import SimpleNamespace
from app.trading.asset_analyzer import AssetAnalyzer
from app.trading.operator_service import OperatorService
from app.trading.operator_api import OperatorAPI

runtime=SimpleNamespace()
manager=SimpleNamespace()
service=OperatorService(runtime,manager,asset_analyzer=AssetAnalyzer())
api=OperatorAPI(service)
code, body=api.handle("POST","/analyze",{"symbol":"spy","asset_class":"etf","price":"500","max_order_notional":"250"})
assert code==200
assert body["symbol"]=="SPY"
assert body["max_quantity"]=="0.5"
assert body["execution_capability"] is False
print("OPERATOR ASSET ANALYSIS: PASS")
