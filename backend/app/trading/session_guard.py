from .risk import RiskRejected


class MarketSessionGuard:
    def __init__(self, session_clock, exchange_calendar):
        self.session_clock = session_clock
        self.exchange_calendar = exchange_calendar

    def validate(self, moment=None):
        session = self.session_clock.session(moment)
        try:
            scheduled_open = self.exchange_calendar.is_open(session.trading_day)
        except RiskRejected:
            raise
        except Exception as exc:
            raise RiskRejected(
                f"Unable to validate market session: {exc}"
            ) from exc

        verified = self.session_clock.session(
            moment,
            market_open=scheduled_open,
        )
        if not verified.regular_hours:
            raise RiskRejected(
                "Order execution is outside verified regular market hours."
            )
        return verified
