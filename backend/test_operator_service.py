from types import SimpleNamespace
from app.trading.operator_service import OperatorService

class Runtime:
    def status(self):
        return SimpleNamespace(started=True,ready=True,kill_switch_active=False,kill_switch_reason="",trading_enabled=False,dry_run=True,open_orders=0)
class Manager:
    def list_bots(self): return []
service=OperatorService(Runtime(),Manager())
assert service.status()["runtime"]["ready"]
assert service.status()["bots"]["configured"]==0
assert service.release_readiness()["ready"] is False
print("OPERATOR CONTRACT: PASS")
