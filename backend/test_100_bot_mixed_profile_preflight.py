from dataclasses import dataclass
from decimal import Decimal
import tempfile
from pathlib import Path

from app.trading.batch_preflight import BotBatchPreflight
from app.trading.bot_registry import BotConfig, BotRegistry
from app.trading.capital_coordinator import CapitalConfig, PortfolioCapitalCoordinator
from app.trading.exposure_ledger import PortfolioExposureLedger
from app.trading.risk import RiskRejected


@dataclass
class Status:
    started: bool = True
    ready: bool = True


class Runtime:
    def status(self):
        return Status()


@dataclass
class Order:
    symbol: str
    notional: Decimal


@dataclass
class Request:
    bot_id: str
    client_order_id: str
    order: Order


def expect_rejected(fn, text):
    try:
        fn()
        raise AssertionError("Expected RiskRejected")
    except RiskRejected as exc:
        assert text in str(exc)


def run():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        registry = BotRegistry(root / "bots.json")
        capital = PortfolioCapitalCoordinator(
            CapitalConfig(Decimal("50000"), Decimal("0")),
            root / "capital.json",
        )
        exposure = PortfolioExposureLedger(root / "exposure.json", Decimal("50000"))
        preflight = BotBatchPreflight(
            registry, Runtime(), capital_coordinator=capital, exposure_ledger=exposure
        )

        requests = []
        profiles = ["conservative", "moderate", "aggressive"]
        classes = ["stock", "etf", "crypto"]
        limits = {
            "conservative": Decimal("250"),
            "moderate": Decimal("375"),
            "aggressive": Decimal("500"),
        }
        for index in range(100):
            profile = profiles[index % 3]
            asset_class = classes[index % 3]
            symbol = f"SYM{index}"
            bot_id = f"bot-{index:03d}"
            registry.upsert(BotConfig(bot_id, asset_class, symbol, profile, True))
            requests.append(
                Request(bot_id, f"order-{index:03d}", Order(symbol, limits[profile]))
            )

        result = preflight.validate(requests)
        assert result["bots"] == 100
        expected = sum((limits[profiles[i % 3]] for i in range(100)), Decimal("0"))
        assert result["requested_notional"] == expected

        # Existing exposure must be included before the first bot can execute.
        exposure.allocate("existing", Decimal("20000"))
        capital.reserve("reserved", Decimal("5000"), Decimal("50000"), invested_capital=Decimal("20000"))
        expect_rejected(lambda: preflight.validate(requests), "capital ceiling")

        # Registry asset class is immutable execution metadata: invalid classes
        # fail at configuration time before a batch can exist.
        expect_rejected(
            lambda: registry.upsert(BotConfig("bad", "option", "BAD", "moderate", True)),
            "asset class",
        )

    print("100-BOT MIXED PROFILE PREFLIGHT: PASS")


if __name__ == "__main__":
    run()
