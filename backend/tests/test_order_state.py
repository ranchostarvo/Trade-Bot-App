from app.trading.order_state import ManagedOrder, OrderState


def test_happy_path_order_lifecycle():
    order = ManagedOrder("order-1")
    for state in (
        OrderState.VALIDATED,
        OrderState.RESERVED,
        OrderState.SUBMITTED,
        OrderState.ACKNOWLEDGED,
        OrderState.FILLED,
    ):
        order.transition(state)
    assert order.state == OrderState.FILLED
    assert order.terminal is True


def test_cannot_skip_required_order_states():
    order = ManagedOrder("order-1")
    try:
        order.transition(OrderState.SUBMITTED)
    except RuntimeError as exc:
        assert "Invalid order transition" in str(exc)
        return
    raise AssertionError("Order skipped validation and reservation.")


def test_rejection_requires_reason():
    order = ManagedOrder("order-1")
    try:
        order.transition(OrderState.REJECTED)
    except RuntimeError as exc:
        assert "require a reason" in str(exc)
        return
    raise AssertionError("Rejected order omitted its reason.")


def test_terminal_order_cannot_restart():
    order = ManagedOrder("order-1")
    order.transition(OrderState.REJECTED, reason="risk rejected")
    assert order.terminal is True
    try:
        order.transition(OrderState.VALIDATED)
    except RuntimeError:
        return
    raise AssertionError("Terminal order was restarted.")
