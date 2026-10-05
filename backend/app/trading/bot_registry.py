import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .risk import RiskRejected


@dataclass(frozen=True)
class BotConfig:
    bot_id: str
    asset_class: str
    symbol: str
    risk_profile: str
    enabled: bool = False


class BotRegistry:
    """Persistent fail-closed configuration registry for up to 100 bots."""

    VALID_ASSET_CLASSES = {"stock", "etf", "crypto"}
    VALID_RISK_PROFILES = {"conservative", "moderate", "aggressive"}

    def __init__(self, path, max_bots=100):
        self.path = Path(path)
        self.max_bots = int(max_bots)
        self._bots = self._read()

    def _validate(self, bot):
        bot_id = str(bot.bot_id or "").strip()
        symbol = str(bot.symbol or "").strip().upper()
        asset_class = str(bot.asset_class or "").strip().lower()
        risk_profile = str(bot.risk_profile or "").strip().lower()
        if not bot_id or not symbol:
            raise RiskRejected("Bot ID and symbol are required.")
        if asset_class not in self.VALID_ASSET_CLASSES:
            raise RiskRejected("Unsupported bot asset class.")
        if risk_profile not in self.VALID_RISK_PROFILES:
            raise RiskRejected("Unsupported bot risk profile.")
        return BotConfig(bot_id, asset_class, symbol, risk_profile, bool(bot.enabled))

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text())
            if not isinstance(raw, dict):
                raise ValueError("bot registry root must be an object")
            bots = {}
            for bot_id, value in raw.items():
                bot = self._validate(BotConfig(**value))
                if bot.bot_id != bot_id:
                    raise ValueError("bot registry key mismatch")
                bots[bot_id] = bot
            if len(bots) > self.max_bots:
                raise ValueError("bot registry exceeds configured limit")
            return bots
        except Exception as exc:
            raise RiskRejected(f"Unable to read bot registry: {exc}") from exc

    def _write(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(
            {key: asdict(value) for key, value in self._bots.items()},
            sort_keys=True,
            indent=2,
        ))
        os.replace(temporary, self.path)

    def upsert(self, bot):
        bot = self._validate(bot)
        if bot.bot_id not in self._bots and len(self._bots) >= self.max_bots:
            raise RiskRejected("Bot registry limit reached.")
        self._bots[bot.bot_id] = bot
        self._write()
        return bot

    def get(self, bot_id):
        return self._bots.get(str(bot_id))

    def all(self):
        return list(self._bots.values())

    def enabled(self):
        return [bot for bot in self._bots.values() if bot.enabled]
