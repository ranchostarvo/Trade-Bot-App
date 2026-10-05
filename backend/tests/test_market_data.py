from app.trading.market_data import AlpacaMarketDataProvider, MarketDataError


class Response:
    def __init__(self, payload, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload


class Session:
    def __init__(self):
        self.headers = {}
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        if url.endswith("/trades/latest"):
            return Response({"trade": {"p": 101.25}})
        return Response({"bars": [{"c": 99.0}, {"c": 100.0}]})


def test_market_data_adapter_is_read_only_and_builds_snapshot():
    session = Session()
    provider = AlpacaMarketDataProvider("key", "secret", session=session)
    snapshot = provider.snapshot("spy")
    assert snapshot.symbol == "SPY"
    assert str(snapshot.price) == "101.25"
    assert str(snapshot.previous_close) == "99.0"
    assert all(call[0].startswith(provider.DATA_URL) for call in session.calls)
    assert not hasattr(provider, "submit_order")


def test_market_data_requires_credentials():
    try:
        AlpacaMarketDataProvider("", "")
    except MarketDataError:
        return
    raise AssertionError("Missing credentials were accepted.")
