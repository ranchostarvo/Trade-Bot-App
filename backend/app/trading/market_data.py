from abc import ABC, abstractmethod
from decimal import Decimal

import requests

from .signal import MarketSnapshot


class MarketDataError(RuntimeError):
    """Raised when read-only market data cannot be obtained safely."""


class MarketDataProvider(ABC):
    @abstractmethod
    def snapshot(self, symbol: str) -> MarketSnapshot:
        raise NotImplementedError


class AlpacaMarketDataProvider(MarketDataProvider):
    """Read-only Alpaca market-data adapter. It cannot submit orders."""

    DATA_URL = "https://data.alpaca.markets"

    def __init__(self, api_key: str, secret_key: str, session=None):
        if not api_key.strip() or not secret_key.strip():
            raise MarketDataError("Market-data credentials are required.")
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": secret_key,
                "Accept": "application/json",
            }
        )

    def _get(self, path: str, params=None):
        try:
            response = self.session.get(
                f"{self.DATA_URL}{path}", params=params, timeout=15
            )
        except requests.RequestException as exc:
            raise MarketDataError(
                f"Unable to obtain market data: {exc}"
            ) from exc
        if not response.ok:
            raise MarketDataError(
                f"Market data returned HTTP {response.status_code}."
            )
        return response.json()

    def snapshot(self, symbol: str) -> MarketSnapshot:
        symbol = symbol.strip().upper()
        if not symbol:
            raise MarketDataError("Symbol is required.")

        latest = self._get(f"/v2/stocks/{symbol}/trades/latest")
        bars = self._get(
            f"/v2/stocks/{symbol}/bars",
            params={"timeframe": "1Day", "limit": 2},
        )

        try:
            price = Decimal(str(latest["trade"]["p"]))
            items = bars["bars"]
            if len(items) < 2:
                raise KeyError("insufficient bars")
            previous_close = Decimal(str(items[-2]["c"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise MarketDataError(
                "Market-data response did not contain required prices."
            ) from exc

        return MarketSnapshot(
            symbol=symbol,
            price=price,
            previous_close=previous_close,
        )
