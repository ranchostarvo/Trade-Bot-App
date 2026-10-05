from app.trading.virtual_broker import VirtualBroker


def run():
    broker = VirtualBroker()
    broker.set_price("SPY", "500")
    order = broker.submit_order({
        "symbol": "SPY", "side": "buy", "client_order_id": "day-1"
    })
    assert order["status"] == "accepted"
    broker.transition("day-1", "partially_filled", "0.5", "500")
    broker.transition("day-1", "filled", "1", "501")
    assert [event["type"] for event in broker.events] == [
        "submitted", "transition", "transition"
    ]

    broker.submit_order({"symbol": "QQQ", "side": "buy", "client_order_id": "day-2"})
    assert broker.expire_open_orders() == 1
    assert broker.get_order_by_client_id("day-2")["status"] == "expired"

    broker.inject_read("outage")
    try:
        broker.get_account()
        raise AssertionError("Expected read outage")
    except ConnectionError:
        pass

    broker.inject_read("rate_limit")
    try:
        broker.get_order_by_client_id("day-1")
        raise AssertionError("Expected rate limit")
    except RuntimeError:
        pass

    broker.inject("after_transmission")
    try:
        broker.submit_order({"symbol": "BTCUSD", "side": "buy", "client_order_id": "ambiguous"})
        raise AssertionError("Expected ambiguous transmission")
    except TimeoutError:
        pass
    recovered = broker.get_order_by_client_id("ambiguous")
    assert recovered["status"] == "accepted"

    broker.inject("before_transmission")
    try:
        broker.submit_order({"symbol": "ETHUSD", "side": "buy", "client_order_id": "never-sent"})
        raise AssertionError("Expected pre-transmission failure")
    except ConnectionError:
        pass
    assert "never-sent" not in broker.orders

    print("VIRTUAL BROKER FAULT MATRIX: PASS")


if __name__ == "__main__":
    run()
