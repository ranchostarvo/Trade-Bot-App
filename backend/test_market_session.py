from datetime import datetime
from zoneinfo import ZoneInfo

from app.trading.market_session import USMarketSessionClock

clock = USMarketSessionClock()
ny = ZoneInfo("America/New_York")

open_session = clock.session(datetime(2026, 10, 5, 10, 0, tzinfo=ny))
assert open_session.regular_hours is True
assert open_session.trading_day.isoformat() == "2026-10-05"

before_open = clock.session(datetime(2026, 10, 5, 8, 0, tzinfo=ny))
assert before_open.regular_hours is False

after_close = clock.session(datetime(2026, 10, 5, 16, 0, tzinfo=ny))
assert after_close.regular_hours is False

weekend = clock.session(datetime(2026, 10, 4, 12, 0, tzinfo=ny))
assert weekend.regular_hours is False

utc = ZoneInfo("UTC")
converted = clock.session(datetime(2026, 10, 5, 14, 0, tzinfo=utc))
assert converted.regular_hours is True

print("=== TRADING APP v2.0 / MARKET SESSION CLOCK ===")
print("Regular session detection: PASS")
print("Pre-market detection: PASS")
print("Post-market detection: PASS")
print("Weekend detection: PASS")
print("Timezone conversion: PASS")
print("Broker interaction: NO")
print("RESULT: PASS")

# An authoritative exchange calendar can close a weekday (holiday).
holiday = clock.session(
    datetime(2026, 12, 25, 10, 0, tzinfo=ny),
    market_open=False,
)
assert holiday.regular_hours is False

print("Authoritative holiday closure override: PASS")
