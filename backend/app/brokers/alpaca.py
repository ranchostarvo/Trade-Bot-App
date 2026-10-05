import os
from dataclasses import dataclass

import requests


class AlpacaError(RuntimeError):
    """Raised when communication with Alpaca fails."""


@dataclass(frozen=True)
class AlpacaConfig:
    api_key: str
    secret_key: str
    base_url: str
    paper: bool

    @classmethod
    def from_env(cls):
        api_key = os.getenv("ALPACA_API_KEY", "").strip()
        secret_key = os.getenv("ALPACA_SECRET_KEY", "").strip()
        base_url = os.getenv(
            "ALPACA_BASE_URL",
            "https://paper-api.alpaca.markets"
        ).rstrip("/")

        paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"

        if not api_key:
            raise AlpacaError("ALPACA_API_KEY is missing.")

        if not secret_key:
            raise AlpacaError("ALPACA_SECRET_KEY is missing.")

        # Paper v1 is paper-only. A false flag or non-paper endpoint is a
        # configuration error, not an alternate operating mode.
        if not paper:
            raise AlpacaError("Safety violation: Paper v1 requires ALPACA_PAPER=true.")

        if base_url != "https://paper-api.alpaca.markets":
            raise AlpacaError(
                "Safety violation: paper mode is not using "
                "the Alpaca paper endpoint."
            )

        return cls(
            api_key=api_key,
            secret_key=secret_key,
            base_url=base_url,
            paper=paper,
        )


class AlpacaClient:
    def __init__(self, config=None):
        self.config = config or AlpacaConfig.from_env()

        self.session = requests.Session()
        self.session.headers.update({
            "APCA-API-KEY-ID": self.config.api_key,
            "APCA-API-SECRET-KEY": self.config.secret_key,
            "Accept": "application/json",
        })

    def _request(self, method, path, **kwargs):
        url = f"{self.config.base_url}{path}"

        try:
            response = self.session.request(
                method,
                url,
                timeout=15,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise AlpacaError(
                f"Unable to communicate with Alpaca: {exc}"
            ) from exc

        if not response.ok:
            raise AlpacaError(
                f"Alpaca returned HTTP {response.status_code}: "
                f"{response.text}"
            )

        return response.json()

    def get_account(self):
        return self._request("GET", "/v2/account")

    def get_order(self, order_id):
        if not order_id or not str(order_id).strip():
            raise AlpacaError("Order ID is required.")

        return self._request(
            "GET",
            f"/v2/orders/{str(order_id).strip()}",
        )

    def get_order_by_client_id(self, client_order_id):
        client_order_id = str(client_order_id or "").strip()
        if not client_order_id:
            raise AlpacaError("Client order ID is required.")

        return self._request(
            "GET",
            "/v2/orders:by_client_order_id",
            params={"client_order_id": client_order_id},
        )

    def get_calendar(self, start, end):
        start = str(start or "").strip()
        end = str(end or "").strip()
        if not start or not end:
            raise AlpacaError("Calendar start and end dates are required.")

        return self._request(
            "GET",
            "/v2/calendar",
            params={"start": start, "end": end},
        )

    def get_position(self, symbol):
        symbol = str(symbol or "").strip().upper()
        if not symbol:
            raise AlpacaError("Symbol is required.")

        return self._request(
            "GET",
            f"/v2/positions/{symbol}",
        )

    def health_check(self):
        account = self.get_account()

        return {
            "connected": True,
            "paper": self.config.paper,
            "status": account.get("status"),
            "trading_blocked": account.get("trading_blocked"),
            "account_blocked": account.get("account_blocked"),
            "buying_power": account.get("buying_power"),
        }

    def submit_order(self, order_payload):
        if not self.config.paper:
            raise AlpacaError(
                "Safety violation: order submission requires paper mode."
            )

        if self.config.base_url != "https://paper-api.alpaca.markets":
            raise AlpacaError(
                "Safety violation: refusing non-paper Alpaca endpoint."
            )

        return self._request(
            "POST",
            "/v2/orders",
            json=order_payload,
        )
