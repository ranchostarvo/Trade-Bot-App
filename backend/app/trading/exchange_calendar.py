from dataclasses import dataclass
from datetime import date, time

from .risk import RiskRejected


@dataclass(frozen=True)
class ExchangeSession:
    trading_day: date
    open_time: time
    close_time: time


class AlpacaExchangeCalendar:
    def __init__(self, broker):
        self.broker = broker

    def get_session(self, trading_day: date):
        day = trading_day.isoformat()
        try:
            rows = self.broker.get_calendar(day, day)
        except Exception as exc:
            raise RiskRejected(
                f"Unable to verify exchange calendar: {exc}"
            ) from exc

        if not isinstance(rows, list):
            raise RiskRejected("Invalid exchange calendar response.")

        row = next(
            (item for item in rows if str(item.get("date") or "") == day),
            None,
        )
        if row is None:
            return None

        try:
            open_time = time.fromisoformat(str(row["open"]))
            close_time = time.fromisoformat(str(row["close"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise RiskRejected(
                "Exchange calendar returned invalid session times."
            ) from exc

        if close_time <= open_time:
            raise RiskRejected("Exchange calendar returned invalid session bounds.")

        return ExchangeSession(
            trading_day=trading_day,
            open_time=open_time,
            close_time=close_time,
        )

    def is_open(self, trading_day: date) -> bool:
        return self.get_session(trading_day) is not None
