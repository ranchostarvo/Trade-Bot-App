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

        # Safety interlock:
        # paper mode must never point at the live endpoint.
        if paper and "paper-api.alpaca.markets" not in base_url:
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

    def get_positions(self):
        return self._request("GET", "/v2/positions")

    def get_order(self, order_id: str):
        if not order_id or not order_id.strip():
            raise AlpacaError("Order ID is required.")
        return self._request("GET", f"/v2/orders/{order_id.strip()}")

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
