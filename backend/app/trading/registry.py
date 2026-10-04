from .lifecycle import BotLifecycle, BotState


class BotRegistry:
    def __init__(self):
        self._bots: dict[str, BotLifecycle] = {}

    def create(self, bot_id: str) -> BotLifecycle:
        bot_id = bot_id.strip()
        if bot_id in self._bots:
            raise ValueError(f"Bot {bot_id} already exists.")
        bot = BotLifecycle(bot_id)
        self._bots[bot_id] = bot
        return bot

    def get(self, bot_id: str) -> BotLifecycle:
        try:
            return self._bots[bot_id]
        except KeyError as exc:
            raise KeyError(f"Unknown bot {bot_id}.") from exc

    def all(self) -> tuple[BotLifecycle, ...]:
        return tuple(self._bots.values())

    def by_state(self, state: BotState) -> tuple[BotLifecycle, ...]:
        return tuple(bot for bot in self._bots.values() if bot.state is state)

    def stop_all(self) -> None:
        for bot in self._bots.values():
            if bot.state not in {BotState.STOPPED, BotState.FAULTED}:
                bot.stop()
            elif bot.state is BotState.FAULTED:
                bot.stop()
