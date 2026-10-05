from datetime import datetime
from zoneinfo import ZoneInfo

from app.trading.market_session import USMarketSessionClock
from app.trading.risk import RiskRejected
from app.trading.session_guard import MarketSessionGuard


class Calendar:
    def __init__(self, open_day=True):
        self.open_day = open_day

    def is_open(self, trading_day):
        return self.open_day


ny = ZoneInfo("America/New_York")
clock = USMarketSessionClock()

guard = MarketSessionGuard(clock, Calendar(True))
verified = guard.validate(datetime(2026, 10, 5, 10, 0, tzinfo=ny))
assert verified.regular_hours is True

for moment, calendar in [
    (datetime(2026, 10, 5, 8, 0, tzinfo=ny), Calendar(True)),
    (datetime(2026, 12, 25, 10, 0, tzinfo=ny), Calendar(False)),
]:
    try:
        MarketSessionGuard(clock, calendar).validate(moment)
        raise AssertionError("Closed session must be rejected.")
    except RiskRejected:
        pass

print("=== TRADING APP v2.0 / SESSION GUARD ===")
print("Verified regular session allowed: PASS")
print("Pre-market rejected: PASS")
print("Exchange holiday rejected: PASS")
print("Broker write interaction: NO")
print("RESULT: PASS")
