from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from app.storage import SQLiteStore


def test_persistent_exposure_survives_restart(tmp_path):
    path = tmp_path / "trading.db"
    store = SQLiteStore(str(path))
    assert store.reserve_exposure_atomically(
        "bot-1", "spy", "100", "100000", "2500", "10"
    )
    restarted = SQLiteStore(str(path))
    assert restarted.load_exposure_reservations("SPY") == {"bot-1": "100"}


def test_multi_connection_exposure_never_exceeds_symbol_limit(tmp_path):
    path = tmp_path / "trading.db"

    def reserve(index):
        return SQLiteStore(str(path)).reserve_exposure_atomically(
            f"bot-{index}", "SPY", Decimal("100"),
            Decimal("100000"), Decimal("2500"), Decimal("10")
        )

    with ThreadPoolExecutor(max_workers=40) as pool:
        results = list(pool.map(reserve, range(100)))

    assert results.count(True) == 25
    reservations = SQLiteStore(str(path)).load_exposure_reservations("SPY")
    total = sum((Decimal(v) for v in reservations.values()), Decimal("0"))
    assert total == Decimal("2500")


def test_equity_percentage_limit_can_be_tighter_than_notional(tmp_path):
    store = SQLiteStore(str(tmp_path / "trading.db"))
    assert store.reserve_exposure_atomically(
        "bot-1", "QQQ", "900", "10000", "2500", "10"
    )
    assert store.reserve_exposure_atomically(
        "bot-2", "QQQ", "200", "10000", "2500", "10"
    ) is False
