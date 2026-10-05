from app.storage import SQLiteStore


def test_order_recovery_context_survives_restart(tmp_path):
    path = str(tmp_path / "trading.db")
    store = SQLiteStore(path)
    store.save_order_recovery_context(
        "order-1", "bot-1", "SPY", "buy", "1.25", "500.10",
        "broker-123",
    )

    recovered = SQLiteStore(path).load_order_recovery_context("order-1")
    assert recovered == {
        "order_id": "order-1",
        "bot_id": "bot-1",
        "symbol": "SPY",
        "side": "buy",
        "quantity": "1.25",
        "estimated_price": "500.10",
        "broker_order_id": "broker-123",
    }


def test_order_recovery_context_requires_complete_request(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    try:
        store.save_order_recovery_context(
            "order-1", "", "SPY", "buy", "1", "100"
        )
    except ValueError as exc:
        assert "Complete order recovery context" in str(exc)
    else:
        raise AssertionError("Expected incomplete recovery context to fail.")
