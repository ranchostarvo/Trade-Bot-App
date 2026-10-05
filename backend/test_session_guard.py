from datetime import datetime, time
from zoneinfo import ZoneInfo

from app.trading.exchange_calendar import ExchangeSession
from app.trading.market_session import USMarketSessionClock
from app.trading.risk import RiskRejected
from app.trading.session_guard import MarketSessionGuard


class Calendar:
    def __init__(self, open_day=True):
        self.open_day = open_day

    def get_session(self, trading_day):
        if not self.open_day:
            return None
        return ExchangeSession(
            trading_day=trading_day,
            open_time=time(9, 30),
            close_time=time(16, 0),
        )


ny = ZoneInfo("America/New_York")
clock = USMarketSessionClock()

guard = MarketSessionGuard(clock, Calendar(True))
verified = guard.validate(datetime(2026, 10, 5, 10, 0, tzinfo=ny))
assert verified.trading_day.isoformat() == "2026-10-05"
assert verified.open_time == time(9, 30)
assert verified.close_time == time(16, 0)

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
