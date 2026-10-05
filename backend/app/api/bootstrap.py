import os
from dataclasses import dataclass
from decimal import Decimal

from app.api.control_plane import ControlPlane
from app.bootstrap import BrokerBootstrap
from app.trading.runtime import TradingRuntime


class ApplicationBootstrapBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class ApplicationContext:
    control_plane: ControlPlane
    broker_backed: bool


def build_application_context(env=None, broker_builder=None):
    """Compose API state without ever enabling broker order submission."""
    env = env or os.environ
    broker_builder = broker_builder or BrokerBootstrap.build
    mode = env.get("TRADING_BOOTSTRAP_MODE", "development").strip().lower()

    if mode == "broker":
        try:
            bootstrap = broker_builder()
        except Exception as exc:
            raise ApplicationBootstrapBlocked(
                "Broker-backed application bootstrap failed."
            ) from exc
        return ApplicationContext(
            control_plane=ControlPlane.build(bootstrap.runtime),
            broker_backed=True,
        )

    if mode != "development":
        raise ApplicationBootstrapBlocked(
            "TRADING_BOOTSTRAP_MODE must be 'development' or 'broker'."
        )

    runtime = TradingRuntime.build(account_cash=Decimal("50000"))
    return ApplicationContext(
        control_plane=ControlPlane.build(runtime),
        broker_backed=False,
    )
