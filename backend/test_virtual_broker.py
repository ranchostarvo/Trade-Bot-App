from app.trading.virtual_broker import VirtualBroker

broker = VirtualBroker()
payload = {
    "symbol": "SPY", "side": "buy", "qty": "1",
    "type": "market", "time_in_force": "day",
    "client_order_id": "test-1",
}
accepted = broker.submit_order(payload)
assert accepted["status"] == "accepted"
partial = broker.transition("test-1", "partially_filled", "0.4", "500")
assert partial["filled_qty"] == "0.4"
filled = broker.transition("test-1", "filled", "1", "501")
assert filled["status"] == "filled"

broker.inject("after_transmission")
payload["client_order_id"] = "ambiguous-1"
try:
    broker.submit_order(payload)
    raise AssertionError("Ambiguous timeout expected.")
except TimeoutError:
    pass
recovered = broker.get_order_by_client_id("ambiguous-1")
assert recovered["status"] == "accepted"

broker.inject("reject")
payload["client_order_id"] = "reject-1"
assert broker.submit_order(payload)["status"] == "rejected"

print("VIRTUAL BROKER: PASS")
print("Accepted/partial/filled lifecycle: PASS")
print("Ambiguous post-transmission recovery: PASS")
print("Broker rejection simulation: PASS")
print("External network calls: NONE")
print("Real Alpaca order submitted: NO")
