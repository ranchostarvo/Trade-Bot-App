from decimal import Decimal

from app.storage import SQLiteStore
from app.trading.resources import DurableResourceCoordinator


def resources(path):
    return DurableResourceCoordinator(
        SQLiteStore(str(path)),
        Decimal("50000"),
        Decimal("100000"),
    )


def test_partial_exposure_release_is_durable(tmp_path):
    path = tmp_path / "trading.db"
    r = resources(path)
    r.reserve_symbol_exposure("bot-1", "spy", Decimal("500"))
    r.release_symbol_exposure("bot-1", "SPY", Decimal("200"))
    assert r.store.load_exposure_reservations("SPY") == {"bot-1": "300"}

    restarted = resources(path)
    assert restarted.store.load_exposure_reservations("SPY") == {"bot-1": "300"}


def test_full_exposure_release_frees_symbol_capacity(tmp_path):
    path = tmp_path / "trading.db"
    r = resources(path)
    for i in range(25):
        r.reserve_symbol_exposure(f"bot-{i}", "SPY", Decimal("100"))

    r.release_symbol_exposure("bot-0", "SPY")
    r.reserve_symbol_exposure("replacement", "SPY", Decimal("100"))

    reservations = r.store.load_exposure_reservations("SPY")
    total = sum((Decimal(v) for v in reservations.values()), Decimal("0"))
    assert total == Decimal("2500")
    assert "bot-0" not in reservations
    assert reservations["replacement"] == "100"
