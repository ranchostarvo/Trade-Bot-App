from datetime import datetime
from zoneinfo import ZoneInfo

from app.trading.exchange_calendar import AlpacaExchangeCalendar
from app.trading.market_session import USMarketSessionClock
from app.trading.risk import RiskRejected
from app.trading.session_guard import MarketSessionGuard


class Broker:
    def __init__(self, close_time):
        self.close_time = close_time

    def get_calendar(self, start, end):
        return [{
            "date": start,
            "open": "09:30",
            "close": self.close_time,
        }]


tz = ZoneInfo("America/New_York")
clock = USMarketSessionClock()
guard = MarketSessionGuard(
    clock,
    AlpacaExchangeCalendar(Broker("13:00")),
)

assert guard.validate(
    datetime(2026, 11, 27, 12, 59, tzinfo=tz)
).close_time.isoformat() == "13:00:00"

try:
    guard.validate(datetime(2026, 11, 27, 13, 0, tzinfo=tz))
    raise AssertionError("Early close boundary must reject execution.")
except RiskRejected:
    pass

try:
    guard.validate(datetime(2026, 11, 27, 15, 0, tzinfo=tz))
    raise AssertionError("Post-close execution must be rejected.")
except RiskRejected:
    pass

print("=== TRADING APP v2.0 / EARLY CLOSE ===")
print("Authoritative close accepted before boundary: PASS")
print("Exact early-close boundary rejected: PASS")
print("Post-close execution rejected: PASS")
print("Broker write interaction: NO")
print("RESULT: PASS")
