from app.storage import SQLiteStore


def test_pending_buy_settles_atomically_into_filled_exposure(tmp_path):
    path = tmp_path / "trading.db"
    store = SQLiteStore(str(path))
    assert store.reserve_pending_exposure("order-1", "bot-1", "SPY", "100")

    assert store.settle_pending_buy_atomically("order-1") is True

    assert store.load_pending_exposure() == {}
    assert store.load_exposure_reservations("SPY") == {"bot-1": "100"}


def test_settlement_adds_to_existing_filled_exposure(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    assert store.reserve_exposure_atomically(
        "bot-1", "SPY", "300", "100000", "2500", "10"
    )
    assert store.reserve_pending_exposure("order-1", "bot-1", "SPY", "100")

    assert store.settle_pending_buy_atomically("order-1") is True
    assert store.load_pending_exposure() == {}
    assert store.load_exposure_reservations("SPY") == {"bot-1": "400"}


def test_missing_pending_order_cannot_be_settled(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    assert store.settle_pending_buy_atomically("missing") is False
    assert store.load_exposure_reservations("SPY") == {}
