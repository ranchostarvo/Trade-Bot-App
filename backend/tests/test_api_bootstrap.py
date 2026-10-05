from types import SimpleNamespace

import pytest

from app.api.bootstrap import (
    ApplicationBootstrapBlocked,
    build_application_context,
)
from app.trading.runtime import TradingRuntime


def test_development_mode_is_broker_disconnected_and_not_ready():
    context = build_application_context(env={"TRADING_BOOTSTRAP_MODE": "development"})
    assert context.broker_backed is False
    assert context.control_plane.trading_ready is False
    assert context.control_plane.fleet.kill_switch.engaged is True


def test_broker_mode_uses_broker_runtime():
    runtime = TradingRuntime.build(account_cash=100, account_equity=100, store=None)

    class Bootstrap:
        pass

    bootstrap = Bootstrap()
    bootstrap.runtime = runtime

    context = build_application_context(
        env={"TRADING_BOOTSTRAP_MODE": "broker"},
        broker_builder=lambda: bootstrap,
    )
    assert context.broker_backed is True
    assert context.control_plane.runtime is runtime


def test_broker_mode_never_silently_falls_back():
    def fail():
        raise RuntimeError("credentials unavailable")

    with pytest.raises(ApplicationBootstrapBlocked, match="failed"):
        build_application_context(
            env={"TRADING_BOOTSTRAP_MODE": "broker"},
            broker_builder=fail,
        )


def test_unknown_mode_fails_closed():
    with pytest.raises(ApplicationBootstrapBlocked, match="must be"):
        build_application_context(env={"TRADING_BOOTSTRAP_MODE": "live"})
