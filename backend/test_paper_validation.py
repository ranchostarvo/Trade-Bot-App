from decimal import Decimal
from types import SimpleNamespace

from app.trading.paper_validation import run_authorized_validation
from app.trading.risk import RiskRejected


class Client:
    def __init__(self, paper=True, url="https://paper-api.alpaca.markets"):
        self.config=SimpleNamespace(paper=paper,base_url=url)
    def get_account(self):
        return {"status":"ACTIVE","trading_blocked":False,"account_blocked":False}


class Engine:
    def __init__(self): self.calls=[]
    def execute(self, order, client_order_id=None):
        self.calls.append((order,client_order_id))
        return {"submitted":True,"status":"accepted"}


e=Engine()
r=run_authorized_validation(e,Client())
assert r["paper"] is True and len(e.calls)==1
assert e.calls[0][0].requested_notional==Decimal("10")
assert e.calls[0][1].startswith("paper-rc-")

for client in [Client(False),Client(True,"https://api.alpaca.markets")]:
    try:
        run_authorized_validation(Engine(),client)
        raise AssertionError("unsafe broker accepted")
    except RiskRejected: pass

try:
    run_authorized_validation(Engine(),Client(),notional="10.01")
    raise AssertionError("oversized validation accepted")
except RiskRejected: pass

print("CONTROLLED PAPER VALIDATION HARNESS: PASS")
