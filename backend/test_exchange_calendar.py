from datetime import date

from app.trading.exchange_calendar import AlpacaExchangeCalendar
from app.trading.risk import RiskRejected


class FakeCalendarBroker:
    def get_calendar(self, start, end):
        assert start == end
        if start == "2026-12-25":
            return []
        return [{"date": start, "open": "09:30", "close": "16:00"}]


calendar = AlpacaExchangeCalendar(FakeCalendarBroker())
assert calendar.is_open(date(2026, 10, 5)) is True
assert calendar.is_open(date(2026, 12, 25)) is False


class BrokenBroker:
    def get_calendar(self, start, end):
        raise RuntimeError("network unavailable")


try:
    AlpacaExchangeCalendar(BrokenBroker()).is_open(date(2026, 10, 5))
    raise AssertionError("Calendar failure must fail closed.")
except RiskRejected:
    pass

print("=== TRADING APP v2.0 / EXCHANGE CALENDAR ===")
print("Scheduled trading day detected: PASS")
print("Holiday closure detected: PASS")
print("Calendar failure fails closed: PASS")
print("Broker write interaction: NO")
print("RESULT: PASS")
