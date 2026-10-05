from datetime import date

from .risk import RiskRejected


class AlpacaExchangeCalendar:
    def __init__(self, broker):
        self.broker = broker

    def is_open(self, trading_day: date) -> bool:
        day = trading_day.isoformat()
        try:
            rows = self.broker.get_calendar(day, day)
        except Exception as exc:
            raise RiskRejected(
                f"Unable to verify exchange calendar: {exc}"
            ) from exc

        if not isinstance(rows, list):
            raise RiskRejected("Invalid exchange calendar response.")

        return any(str(row.get("date") or "") == day for row in rows)
