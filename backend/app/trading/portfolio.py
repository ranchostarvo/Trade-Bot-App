from dataclasses import dataclass
from decimal import Decimal
from threading import RLock


class ExposureRejected(RuntimeError):
    """Raised when aggregate portfolio exposure exceeds a hard limit."""


@dataclass(frozen=True)
class ExposureConfig:
    max_symbol_notional: Decimal = Decimal("2500")
    max_symbol_pct: Decimal = Decimal("10")


class PortfolioCoordinator:
    """Tracks aggregate planned exposure across all bots."""

    def __init__(self, account_equity: Decimal, config=None):
        if account_equity <= 0:
            raise ValueError("Account equity must be greater than zero.")
        self.account_equity = account_equity
        self.config = config or ExposureConfig()
        self._exposure: dict[str, dict[str, Decimal]] = {}
        self._lock = RLock()

    def _symbol_total(self, symbol: str) -> Decimal:
        return sum(self._exposure.get(symbol, {}).values(), Decimal("0"))

    def reserve_exposure(
        self, bot_id: str, symbol: str, notional: Decimal
    ) -> Decimal:
        with self._lock:
            return self._reserve_exposure_locked(bot_id, symbol, notional)

    def _reserve_exposure_locked(
        self, bot_id: str, symbol: str, notional: Decimal
    ) -> Decimal:
        bot_id = bot_id.strip()
        symbol = symbol.strip().upper()
        if not bot_id or not symbol:
            raise ExposureRejected("bot_id and symbol are required.")
        if notional <= 0:
            raise ExposureRejected("Exposure notional must be greater than zero.")

        current = self._symbol_total(symbol)
        proposed = current + notional
        pct = (proposed / self.account_equity) * Decimal("100")

        if proposed > self.config.max_symbol_notional:
            raise ExposureRejected(
                f"{symbol} aggregate exposure ${proposed} exceeds "
                f"${self.config.max_symbol_notional} limit."
            )
        if pct > self.config.max_symbol_pct:
            raise ExposureRejected(
                f"{symbol} aggregate exposure {pct:.4f}% exceeds "
                f"{self.config.max_symbol_pct}% equity limit."
            )

        bot_exposure = self._exposure.setdefault(symbol, {})
        bot_exposure[bot_id] = bot_exposure.get(bot_id, Decimal("0")) + notional
        return proposed

    def release_exposure(
        self, bot_id: str, symbol: str, notional: Decimal | None = None
    ) -> Decimal:
        symbol = symbol.strip().upper()
        positions = self._exposure.get(symbol, {})
        if bot_id not in positions:
            raise ExposureRejected(
                f"No {symbol} exposure exists for bot {bot_id}."
            )

        held = positions[bot_id]
        release = held if notional is None else notional
        if release <= 0 or release > held:
            raise ExposureRejected("Invalid exposure release amount.")

        remaining = held - release
        if remaining == 0:
            del positions[bot_id]
        else:
            positions[bot_id] = remaining
        if not positions:
            self._exposure.pop(symbol, None)
        return self._symbol_total(symbol)

    def symbol_exposure(self, symbol: str) -> Decimal:
        return self._symbol_total(symbol.strip().upper())

    def snapshot(self) -> dict[str, str]:
        return {
            symbol: str(self._symbol_total(symbol))
            for symbol in sorted(self._exposure)
        }
