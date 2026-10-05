from app.brokers.alpaca import AlpacaClient, AlpacaConfig, AlpacaError

KEY="test-key"
SECRET="test-secret"
PAPER="https://paper-api.alpaca.markets"

# Exact Paper-v1 endpoint is accepted without making a network request.
client=AlpacaClient(AlpacaConfig(KEY, SECRET, PAPER, True))
assert client.config.paper is True

for url, paper in [
    ("https://api.alpaca.markets", True),
    ("https://paper-api.alpaca.markets.evil.example", True),
    ("http://paper-api.alpaca.markets", True),
    (PAPER, False),
]:
    config=AlpacaConfig(KEY, SECRET, url, paper)
    try:
        client=AlpacaClient(config)
        client.submit_order({"symbol":"SPY"})
        raise AssertionError("Unsafe Alpaca configuration accepted")
    except AlpacaError:
        pass

print("ALPACA PAPER BOUNDARY: PASS")
