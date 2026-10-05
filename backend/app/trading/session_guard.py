from .risk import RiskRejected


class MarketSessionGuard:
    def __init__(self, session_clock, exchange_calendar):
        self.session_clock = session_clock
        self.exchange_calendar = exchange_calendar

    def validate(self, moment=None):
        moment = moment or self.session_clock.now()
        local = moment.astimezone(self.session_clock.timezone)
        trading_day = local.date()

        try:
            exchange_session = self.exchange_calendar.get_session(trading_day)
        except RiskRejected:
            raise
        except Exception as exc:
            raise RiskRejected(
                f"Unable to validate market session: {exc}"
            ) from exc

        if exchange_session is None:
            raise RiskRejected(
                "Order execution is outside a verified exchange session."
            )

        current_time = local.time().replace(tzinfo=None)
        if not (
            exchange_session.open_time
            <= current_time
            < exchange_session.close_time
        ):
            raise RiskRejected(
                "Order execution is outside verified regular market hours."
            )

        return exchange_session
