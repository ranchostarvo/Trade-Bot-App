from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class MarketSession:
    trading_day: object
    regular_hours: bool


class USMarketSessionClock:
    timezone = ZoneInfo("America/New_York")
    open_time = time(9, 30)
    close_time = time(16, 0)

    def now(self):
        return datetime.now(self.timezone)

    def session(self, moment=None, market_open=None):
        moment = moment or self.now()
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=self.timezone)
        else:
            moment = moment.astimezone(self.timezone)

        weekday = moment.weekday() < 5
        scheduled_open = weekday if market_open is None else bool(market_open)
        regular_hours = (
            scheduled_open
            and self.open_time <= moment.time().replace(tzinfo=None) < self.close_time
        )
        return MarketSession(
            trading_day=moment.date(),
            regular_hours=regular_hours,
        )
