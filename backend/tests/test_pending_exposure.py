from app.storage import SQLiteStore


def test_pending_exposure_survives_restart(tmp_path):
    path = tmp_path / "trading.db"
    store = SQLiteStore(str(path))
    assert store.reserve_pending_exposure("order-1", "bot-1", "spy", "100")

    restarted = SQLiteStore(str(path))
    assert restarted.load_pending_exposure() == {
        "order-1": {
            "bot_id": "bot-1",
            "symbol": "SPY",
            "notional": "100",
        }
    }


def test_pending_exposure_is_unique_per_order(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    assert store.reserve_pending_exposure("order-1", "bot-1", "SPY", "100")
    assert store.reserve_pending_exposure("order-1", "bot-2", "SPY", "100") is False


def test_pending_exposure_can_be_released(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    store.reserve_pending_exposure("order-1", "bot-1", "SPY", "100")
    assert store.release_pending_exposure("order-1") is True
    assert store.load_pending_exposure() == {}
