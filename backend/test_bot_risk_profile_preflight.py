from dataclasses import dataclass
from decimal import Decimal
import tempfile
from pathlib import Path

from app.trading.batch_preflight import BotBatchPreflight
from app.trading.bot_registry import BotConfig, BotRegistry
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
        registry = BotRegistry(Path(directory) / "bots.json")
        registry.upsert(BotConfig("c", "stock", "SPY", "conservative", True))
        registry.upsert(BotConfig("m", "etf", "QQQ", "moderate", True))
        registry.upsert(BotConfig("a", "crypto", "BTCUSD", "aggressive", True))
        preflight = BotBatchPreflight(registry, Runtime())

        result = preflight.validate([
            Request("c", "c1", Order("SPY", Decimal("250"))),
            Request("m", "m1", Order("QQQ", Decimal("375"))),
            Request("a", "a1", Order("BTCUSD", Decimal("500"))),
        ])
        assert result["bots"] == 3
        assert result["requested_notional"] == Decimal("1125")

        expect_rejected(
            lambda: preflight.validate([Request("c", "c2", Order("SPY", Decimal("250.01")))]),
            "conservative",
        )
        expect_rejected(
            lambda: preflight.validate([Request("m", "m2", Order("QQQ", Decimal("375.01")))]),
            "moderate",
        )
        expect_rejected(
            lambda: preflight.validate([Request("a", "a2", Order("BTCUSD", Decimal("500.01")))]),
            "aggressive",
        )
    print("BOT RISK PROFILE PREFLIGHT: PASS")


if __name__ == "__main__":
    run()
