from decimal import Decimal
from app.trading.asset_analyzer import AssetAnalyzer
from app.trading.risk import RiskRejected

a=AssetAnalyzer()
r=a.analyze("spy","etf","500","250")
assert r.symbol=="SPY" and r.max_quantity==Decimal("0.5")
for args in [("", "stock", 1, 1),("X","option",1,1),("X","stock",0,1),("X","stock",1,0)]:
    try:
        a.analyze(*args); raise AssertionError("unsafe analysis accepted")
    except RiskRejected: pass
print("ASSET ANALYZER: PASS")
