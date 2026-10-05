import pytest

from app.brokers.alpaca import AlpacaError
from app.trading.reconciliation import AlpacaReconciler


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.requested = None

    def get_order(self, order_id):
        self.requested = order_id
        return self.response


def test_order_status_is_read_only_and_normalized():
    client = FakeClient({"status": "FILLED"})
    status = AlpacaReconciler(client).order_status("broker-order-1")
    assert status == "filled"
    assert client.requested == "broker-order-1"


def test_order_status_requires_status_field():
    with pytest.raises(AlpacaError, match="missing status"):
        AlpacaReconciler(FakeClient({})).order_status("broker-order-1")


def test_order_status_requires_object_response():
    with pytest.raises(AlpacaError, match="must be an object"):
        AlpacaReconciler(FakeClient([])).order_status("broker-order-1")
