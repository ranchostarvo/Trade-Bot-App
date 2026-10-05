from app.brokers.alpaca import (
    AlpacaClient,
    AlpacaConfig,
    AlpacaError,
)


print(
    "=== TRADING APP v2.0 / "
    "PAPER ORDER INTERFACE ==="
)


class FakePaperClient(AlpacaClient):
    def __init__(self):
        self.config = AlpacaConfig(
            api_key="TEST",
            secret_key="TEST",
            base_url=(
                "https://paper-api.alpaca.markets"
            ),
            paper=True,
        )
        self.captured = None

    def _request(self, method, path, **kwargs):
        self.captured = {
            "method": method,
            "path": path,
            "kwargs": kwargs,
        }

        return {
            "id": "FAKE-PAPER-ORDER",
            "status": "accepted",
        }


client = FakePaperClient()

payload = {
    "symbol": "SPY",
    "qty": "1",
    "side": "buy",
    "type": "market",
    "time_in_force": "day",
}

response = client.submit_order(payload)

assert response["id"] == "FAKE-PAPER-ORDER"
assert client.captured["method"] == "POST"
assert client.captured["path"] == "/v2/orders"

print("Paper endpoint requirement: PASS")
print("Order request construction: PASS")
print("Fake broker submission path: PASS")


class FakeLiveClient(FakePaperClient):
    def __init__(self):
        self.config = AlpacaConfig(
            api_key="TEST",
            secret_key="TEST",
            base_url="https://api.alpaca.markets",
            paper=False,
        )


try:
    FakeLiveClient().submit_order(payload)
    raise AssertionError(
        "Live endpoint was not rejected."
    )
except AlpacaError:
    print("Live endpoint rejected: PASS")


print("REAL ALPACA ORDER SUBMITTED: NO")
print("RESULT: PASS")
